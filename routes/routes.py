from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, login_manager
from models.models import User, Asset, Funcionario,HtmlFile
from forms.forms import LoginForm, UploadFileForm, FilterForm, AlterarStatusForm, UpdateProfileForm
import io, os, base64, re
import pandas as pd
from werkzeug.utils import secure_filename
from ldap3 import Server, Connection, ALL, NTLM
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from typing import Dict, List, Union, Optional

routes = Blueprint('routes', __name__)

SheetDict = Dict[str, pd.DataFrame]

@routes.route('/totvs')
@login_required  # Se quiser que apenas usuários autenticados acessem
def totvs():
    return render_template('totvs.html')  # Renderiza o template totvs.html
def init_db():
    db.create_all()  # Cria as tabelas no banco de dados
    print("Banco de dados inicializado.")

# Função para carregar os arquivos HTML no banco de dados
def load_html_files_to_db():
    html_folder = 'static/paginas_html'
    print(f"Tentando carregar arquivos da pasta: {html_folder}")
    
    if not os.path.exists(html_folder):
        print(f"Pasta {html_folder} não encontrada.")
        return

    # Iterar sobre todos os arquivos HTML na pasta
    for filename in os.listdir(html_folder):
        if filename.endswith('.html'):
            filepath = os.path.join(html_folder, filename)
            print(f"Lendo arquivo: {filepath}")
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
                try:
                    # Verificar se o arquivo já existe no banco
                    existing_file = HtmlFile.query.filter_by(filename=filename).first()
                    if not existing_file:
                        new_file = HtmlFile(filename=filename, content=content)
                        db.session.add(new_file)
                        db.session.commit()
                        print(f"Arquivo {filename} carregado no banco de dados.")
                    else:
                        print(f"Arquivo {filename} já está no banco de dados. Ignorando.")
                except Exception as e:
                    db.session.rollback()
                    print(f"Erro ao inserir o arquivo {filename}: {e}")
@routes.route('/admin/load_html_files')
def admin_load_html_files():
    load_html_files_to_db()
    return "Arquivos HTML carregados no banco de dados."

# Função para buscar arquivos com base no termo de pesquisa
def search_files(search_term):
    search_results = []
    pattern = re.compile(r"_-_(.{3})(.*)", re.IGNORECASE)  # Captura os três primeiros caracteres após "_-_"

    search_term = search_term.replace(" ", "_")  # Substitui espaços por underscores para a busca

    files = HtmlFile.query.all()  # Busca todos os arquivos HTML do banco de dados
    for file in files:
        filename = file.filename
        match = pattern.search(filename)  # Verifica se o nome corresponde ao padrão
        if match:
            three_char_prefix = match.group(1)  # Três caracteres após "_-_"
            rest_of_name = match.group(2)  # O restante do nome
            search_string = three_char_prefix + rest_of_name

            if re.search(search_term, search_string, re.IGNORECASE):
                search_results.append(filename)  # Adiciona o arquivo completo se houver correspondência

    return search_results

# Rota para a busca
@routes.route('/search', methods=['POST'])
def search():
    search_term = request.json.get('search_term', '').strip()
    results = []
    if search_term:
        results = search_files(search_term)  # Busca usando a função

    return jsonify(results)

@routes.route('/grafico_status')
def grafico_status() -> str:
    # Contagem de funcionários por status
    status_contagem: Dict[str, int] = {
        'ATIVO': Funcionario.query.filter_by(status='ATIVO').count(),
        'DESATIVADO': Funcionario.query.filter_by(status='DESATIVADO').count(),
        'FERIAS': Funcionario.query.filter_by(status='FERIAS').count()
    }
    
    # Total de funcionários
    total_funcionarios: int = sum(status_contagem.values())
    
    # Busca os nomes dos funcionários que estão de férias e desativados
    funcionarios_ferias = Funcionario.query.filter_by(status='FERIAS').all()
    nomes_ferias = [f.nome for f in funcionarios_ferias]  # Extraindo apenas os nomes

    funcionarios_desativados = Funcionario.query.filter_by(status='DESATIVADO').all()
    nomes_desativados = [f.nome for f in funcionarios_desativados]  # Extraindo os nomes dos desativados
    
    # Preparando os dados para o gráfico
    labels: List[str] = list(status_contagem.keys())
    values: List[int] = list(status_contagem.values())
    
    # Criando o gráfico
    fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
    ax.bar(labels, values, color=['#4CAF50', '#FF5722', '#FFC107'], edgecolor='black')
    ax.set_title('Distribuição de Status dos Funcionários', fontsize=14, weight='bold')
    ax.set_ylabel('Número de Funcionários', fontsize=12)
    ax.set_xlabel('Status', fontsize=12)
    
    # Adicionando os valores em cima das barras
    for i, v in enumerate(values):
        ax.text(i, v + 0.5, str(v), ha='center', fontsize=12, weight='bold')
    
    # Salvando a imagem do gráfico em memória
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    graph_url: str = base64.b64encode(img.getvalue()).decode()
    plt.close()
    
    # Renderizando o template e passando a lista de funcionários de férias e desativados
    return render_template('grafico_status.html', 
                           graph_url=graph_url, 
                           status_contagem=status_contagem, 
                           total_funcionarios=total_funcionarios,
                           funcionarios_ferias=nomes_ferias,
                           funcionarios_desativados=nomes_desativados)


def load_excel_sheets() -> SheetDict:
    excel_path: str = os.path.join(current_app.config['UPLOAD_FOLDER'], 'ControleCusto.xlsx')
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Arquivo {excel_path} não encontrado.")
    
    xls = pd.ExcelFile(excel_path)
    sheets: SheetDict = {sheet_name: xls.parse(sheet_name) for sheet_name in xls.sheet_names}
    
    return sheets

@routes.route('/sheet/<sheet_name>')
def show_sheet(sheet_name: str) -> Union[str, tuple]:
    try:
        sheets: SheetDict = load_excel_sheets()
    except FileNotFoundError as e:
        return str(e), 404
    
    df: Optional[pd.DataFrame] = sheets.get(sheet_name)
    if df is None:
        return f"Aba '{sheet_name}' não encontrada", 404
    
    return render_template('sheet.html', data=df.to_html(classes='table table-striped'), sheet_name=sheet_name, sheets=sheets)

@login_manager.user_loader
def load_user(user_id: int) -> Optional[User]:
    return User.query.get(int(user_id))

@routes.route('/')
def home() -> str:
    if current_user.is_authenticated:
        return redirect(url_for('routes.listar_ativos'))
    return redirect(url_for('routes.login'))

@routes.route('/profile', methods=['GET', 'POST'])
@login_required
def profile() -> str:
    form: UpdateProfileForm = UpdateProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        
        if form.profile_pic.data:
            pic_filename: str = secure_filename(f'{current_user.id}_{form.profile_pic.data.filename}')
            pic_path: str = os.path.join(current_app.config['PROFILE_PICS_FOLDER'], pic_filename)
            
            if not os.path.exists(current_app.config['PROFILE_PICS_FOLDER']):
                os.makedirs(current_app.config['PROFILE_PICS_FOLDER'])
            
            form.profile_pic.data.save(pic_path)
            current_user.profile_pic = pic_filename
        
        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('routes.profile'))
    
    elif request.method == 'GET':
        form.username.data = current_user.username
    
    return render_template('profile.html', form=form)

@routes.route('/login', methods=['GET', 'POST'])
def login() -> str:
    form: LoginForm = LoginForm()
    if form.validate_on_submit():
        username: str = form.username.data
        password: str = form.password.data
        ldap_host: Optional[str] = current_app.config['LDAP_HOST']
        
        if not ldap_host:
            flash('O servidor LDAP não está configurado.', 'danger')
            return redirect(url_for('routes.login'))
        
        server = Server(ldap_host, get_info=ALL)
        DOMAIN = 'emiteli.com.br'
        user_with_domain = f"{DOMAIN}\\{username}"
        conn = Connection(server, user=user_with_domain, password=password, authentication=NTLM)
        
        if conn.bind():
            user = User.query.filter_by(username=username).first()
            if not user:
                user = User(username=username)
                db.session.add(user)
                db.session.commit()
            
            login_user(user)
            flash('Login bem-sucedido!', 'success')
            return redirect(url_for('routes.listar_ativos'))
        else:
            flash('Falha na autenticação. Verifique suas credenciais.', 'danger')
    
    return render_template('login.html', form=form)

@routes.route('/logout')
@login_required
def logout() -> str:
    logout_user()
    return redirect(url_for('routes.login'))

@routes.route('/listar_ativos', methods=['GET', 'POST'])
@login_required
def listar_ativos():
    form = FilterForm()
    query = Asset.query
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
    ativos = query.all()
    return render_template('listar_ativos.html', form=form, ativos=ativos)

@routes.route('/upload_and_process', methods=['GET', 'POST'])
@login_required
def upload_and_process():
    form = UploadFileForm()
    excel_folder = current_app.config['EXCEL_FOLDER']  
    planilhas_disponiveis = os.listdir(excel_folder)
    df_filtered = None
    
    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)

        if not filename.endswith(('.xls', '.xlsx')):
            flash('Formato de arquivo inválido. Apenas arquivos .xls ou .xlsx são permitidos.', 'danger')
            return redirect(url_for('routes.upload_and_process'))
        
        file_path = os.path.join(excel_folder, filename)
        file.save(file_path)
        flash('Arquivo Excel carregado com sucesso!', 'success')
    
    if request.method == 'POST' and 'tipo_banco' in request.form:
        selected_file = form.file.data.filename if form.file.data else request.form['planilha']
        file_path = os.path.join(excel_folder, selected_file)
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
                    
                    if existing_asset:
                        # Atualiza o registro existente
                        existing_asset.filial = row['Filial']
                        existing_asset.grupo = row['Grupo']
                        existing_asset.classificacao = row['Classificac.']
                        existing_asset.item = row['Item']
                        existing_asset.data_aquisicao = pd.to_datetime(row['Dt. Aquisição'], errors='coerce').date() if row['Dt. Aquisição'] else None
                        existing_asset.quantidade = row['Quantidade']
                        existing_asset.descricao_sintetica = row['Descr. Sint.']
                        existing_asset.numero_placa = row['Num. Placa']
                        existing_asset.codigo_fornecedor = row['Cod. Fornec.']
                        existing_asset.loja_fornecedor = row['Loja Fornec.']
                        existing_asset.nota_fiscal = row['Nota Fiscal']
                    else:
                        # Adiciona um novo registro se não existir
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
                    
                    if existing_funcionario:
                        # Atualiza o registro existente
                        existing_funcionario.status = row['STATUS'] if row['STATUS'] else None
                        existing_funcionario.departamento = row['DEPARTAMENTO'] if row['DEPARTAMENTO'] else None
                        existing_funcionario.nome = row['NOME'] if row['NOME'] else None
                        existing_funcionario.licencas = row['LICENCAS'] if row['LICENCAS'] else None
                        existing_funcionario.cargo = row['CARGO'] if row['CARGO'] else None
                    else:
                        # Adiciona um novo registro se não existir
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
            flash('Dados foram atualizados com sucesso no banco de dados.', 'success')
        
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