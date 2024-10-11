from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file 
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, login_manager 
from models.models import User,  Asset, Funcionario
from forms.forms import LoginForm, UploadFileForm,  FilterForm, AlterarStatusForm
import io, os
import pandas as pd
from werkzeug.utils import secure_filename
from ldap3 import Server, Connection, ALL, NTLM

routes = Blueprint('routes', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@routes.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('routes.listar_ativos'))
    return redirect(url_for('routes.login'))

@routes.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        ldap_host = current_app.config['LDAP_HOST']
        if not ldap_host:
            flash('O servidor LDAP não está configurado.', 'danger')
            return redirect(url_for('routes.login'))

        server = Server(ldap_host, get_info=ALL)
        DOMAIN = 'emiteli.com.br'
        user_with_domain = f"{DOMAIN}\\{username}"

        conn = Connection(server, user=user_with_domain, password=password, authentication=NTLM)

        if conn.bind():  # Tentativa de autenticar via LDAP
            user = User(username)  # Cria um objeto de usuário
            login_user(user)  # Logando o usuário
            flash('Login bem-sucedido!', 'success')
            return redirect(url_for('routes.listar_ativos'))  # Redireciona para a lista de ativos
        else:
            flash('Falha na autenticação. Verifique suas credenciais.', 'danger')

    return render_template('login.html', form=form)



@routes.route('/logout')
def logout():
    logout_user()
    flash('Você foi desconectado com sucesso.', 'success')
    return redirect(url_for('routes.login'))


@routes.route('/listar_ativos', methods=['GET', 'POST'])
@login_required
def listar_ativos():
    form = FilterForm()

    # Consulta inicial, sem filtros
    query = Asset.query

    # Aplicar os filtros baseados nos campos do formulário
    if form.validate_on_submit():
        if form.filial.data:
            query = query.filter(Asset.filial.ilike(f'%{form.filial.data}%'))
        if form.grupo.data:
            query = query.filter_by(grupo=form.grupo.data)
        if form.classificacao.data:
            query = query.filter(Asset.classificacao.ilike(f'%{form.classificacao.data}%'))
        if form.descricao_sintetica.data:
            query = query.filter(Asset.descricao_sintetica.ilike(f'%{form.descricao_sintetica.data}%'))
        if form.codigo_bem.data:
            query = query.filter(Asset.codigo_bem.ilike(f'%{form.codigo_bem.data}%'))
        if form.nota_fiscal.data:
            query = query.filter_by(nota_fiscal=form.nota_fiscal.data)

    # Executar a consulta
    ativos = query.all()
    return render_template('listar_ativos.html', form=form, ativos=ativos)

@routes.route('/upload_and_process', methods=['GET', 'POST'])
@login_required
def upload_and_process():
    form = UploadFileForm()
    planilhas_disponiveis = os.listdir(current_app.config['UPLOAD_FOLDER']) 
    df_filtered = None

    if form.validate_on_submit():
        
        file = form.file.data
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        file.save(file_path)
        flash('Arquivo Excel carregado com sucesso!', 'success')

    if request.method == 'POST' and 'tipo_banco' in request.form:
        
        selected_file = form.file.data.filename if form.file.data else request.form['planilha']
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], selected_file)
        tipo_banco = request.form['tipo_banco']

        if not os.path.exists(file_path):
            flash(f'O arquivo {selected_file} não foi encontrado.', 'danger')
            return render_template('upload_and_process.html', form=form, planilhas_disponiveis=planilhas_disponiveis, df_filtered=df_filtered)

        try:
            
            df_cleaned = pd.read_excel(file_path, header=0)
            df_cleaned = df_cleaned.dropna(how='all', axis=1)
            df_cleaned = df_cleaned.where(df_cleaned.notnull(), None)

            
            if tipo_banco == 'asset':
                df_filtered = df_cleaned.iloc[:, [0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12]]
                df_filtered.columns = ['Filial', 'Grupo', 'Classificac.', 'Cod. do Bem', 'Item', 'Dt. Aquisição', 'Quantidade', 'Descr. Sint.', 'Num. Placa', 'Cod. Fornec.', 'Loja Fornec.', 'Nota Fiscal']

                for index, row in df_filtered.iterrows():
                    existing_asset = Asset.query.filter_by(codigo_bem=row['Cod. do Bem']).first()

                    if not existing_asset:
                        new_asset = Asset(
                            filial=row['Filial'],
                            grupo=row['Grupo'],
                            classificacao=row['Classificac.'],
                            codigo_bem=row['Cod. do Bem'],
                            item=row['Item'],
                            data_aquisicao=pd.to_datetime(row['Dt. Aquisição'], errors='coerce').date() if row['Dt. Aquisição'] else None,
                            quantidade=row['Quantidade'],
                            descricao_sintetica=row['Descr. Sint.'],
                            numero_placa=row['Num. Placa'],
                            codigo_fornecedor=row['Cod. Fornec.'],
                            loja_fornecedor=row['Loja Fornec.'],
                            nota_fiscal=row['Nota Fiscal']
                        )
                        db.session.add(new_asset)

            elif tipo_banco == 'funcionario':
                df_filtered = df_cleaned.iloc[:, [0, 1, 2, 3, 4, 5]]
                df_filtered.columns = ['STATUS', 'DEPARTAMENTO', 'NOME', 'LICENCAS', 'CARGO', 'EMAIL']

                for index, row in df_filtered.iterrows():
                    if not row['DEPARTAMENTO'] and not row['NOME'] and not row['EMAIL']:
                        continue  

                    existing_funcionario = Funcionario.query.filter_by(email=row['EMAIL']).first()

                    if not existing_funcionario:
                        new_funcionario = Funcionario(
                            status=row['STATUS'] if row['STATUS'] else None,
                            departamento=row['DEPARTAMENTO'] if row['DEPARTAMENTO'] else None,
                            nome=row['NOME'] if row['NOME'] else None,
                            licencas=row['LICENCAS'] if row['LICENCAS'] else None,
                            cargo=row['CARGO'] if row['CARGO'] else None,
                            email=row['EMAIL'] if row['EMAIL'] else None
                        )
                        db.session.add(new_funcionario)

            db.session.commit()
            flash('Dados foram inseridos com sucesso no banco de dados.', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao processar o arquivo: {str(e)}', 'danger')

    return render_template('upload_and_process.html', form=form, planilhas_disponiveis=planilhas_disponiveis, df_filtered=df_filtered)


@routes.route('/listar_funcionarios', methods=['GET', 'POST'])
@login_required
def listar_funcionarios():
    form = AlterarStatusForm()
    nome = request.args.get('nome', '')  

    if nome:
        funcionarios = Funcionario.query.filter(Funcionario.nome.ilike(f'%{nome}%')).all()
    else:
        funcionarios = Funcionario.query.all()

    
    if form.validate_on_submit() and request.method == 'POST':
        funcionario_id = request.form.get('funcionario_id')  
        funcionario = Funcionario.query.get(funcionario_id)

        if funcionario:
            novo_status = form.novo_status.data
            funcionario.status = novo_status

            try:
                db.session.commit()
                flash('Status alterado com sucesso!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao salvar no banco: {str(e)}', 'danger')
        else:
            flash('Funcionário não encontrado.', 'danger')

        return redirect(url_for('routes.listar_funcionarios', nome=nome))  

    return render_template('listar_funcionarios.html', funcionarios=funcionarios, form=form)

@routes.route('/alterar_status/<int:funcionario_id>', methods=['POST'])
@login_required
def alterar_status(funcionario_id):
    form = AlterarStatusForm()

    if form.validate_on_submit():  
        novo_status = form.novo_status.data  
        funcionario = Funcionario.query.get(funcionario_id)  

        if funcionario:
            funcionario.status = novo_status  
            try:
                db.session.commit()  
                flash('Status alterado com sucesso!', 'success')
            except Exception as e:
                db.session.rollback()  
                flash(f'Erro ao salvar no banco: {str(e)}', 'danger')
        else:
            flash('Funcionário não encontrado.', 'danger')

    return redirect(url_for('routes.listar_funcionarios'))  

@routes.route('/exportar_funcionarios', methods=['GET'])
@login_required
def exportar_funcionarios():
    funcionarios = Funcionario.query.all()  

    data = {
        'Status': [funcionario.status for funcionario in funcionarios],
        'Departamento': [funcionario.departamento for funcionario in funcionarios],
        'Nome': [funcionario.nome for funcionario in funcionarios],
        'Licenças': [funcionario.licencas for funcionario in funcionarios],
        'Cargo': [funcionario.cargo for funcionario in funcionarios],
        'Email': [funcionario.email for funcionario in funcionarios]
    }
    df = pd.DataFrame(data)

    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Funcionarios')
    
    output.seek(0)  

    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
                     as_attachment=True, download_name='funcionarios_exportados.xlsx')