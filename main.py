from flask import Flask, render_template, redirect, request, flash, url_for, session, send_file, send_from_directory
import fdb
from flask_bcrypt import generate_password_hash, check_password_hash
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = 'Brabo'

host = 'localhost'
database = r'C:\Users\Aluno\Desktop\PauloH\119\pasta-banco\BANCO.FDB'
user = 'sysdba'
password = 'sysdba'

con = fdb.connect(host=host, user=user, password=password, database=database)

@app.route('/')
def index():
    cursor = con.cursor()
    cursor.execute("SELECT * FROM USUARIO")
    usuarios = cursor.fetchall()
    cursor.close()
    return render_template('index.html', usuarios=usuarios)

@app.route('/novo')
def novo():
    if "id_usuario" not in session:
        flash('Você precisa estar logado para criar um livro.', 'error')
        return redirect(url_for('index'))
    return render_template('novo.html', titulo='Novo livro')

@app.route('/criar', methods=['POST'])
def criar():
    # pega os dados do formulário
    titulo = request.form['titulo']
    autor = request.form['autor']
    ano_publicacao = request.form['ano_publicacao']
    cursor = con.cursor()

    try:
        cursor.execute("SELECT 1 FROM livro WHERE titulo = ?", (titulo,))
        if cursor.fetchone():
            flash('Livro já cadastrado', 'error')
            return redirect(url_for('novo'))

        cursor.execute('''INSERT INTO livro (titulo, autor, ano_publicacao)
                              VALUES (?, ?, ?) RETURNING id_livro''', (titulo, autor, ano_publicacao))

        id_livro = cursor.fetchone()[0]
        con.commit()

        arquivo = request.files['arquivo']
        
        if arquivo:
            arquivo.save(f'Uploads/capa{id_livro}.jpg')
    finally:
        cursor.close()
    flash("Livro cadastrado com sucesso!", 'success')
    return redirect(url_for('acervo'))


@app.route('/atualizar')
def atualizar():
    return render_template('editar.html', titulo='Editar livro')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    cursor = con.cursor() # abre cursor
    cursor.execute("SELECT * FROM LIVRO WHERE id_livro = ?", (id,))
    livro = cursor.fetchone()

    if not livro:
        cursor.close()
        flash("Livro não encontrado", 'error')
        return redirect(url_for('acervo'))

    if request.method == 'POST':
        titulo = request.form['titulo']
        autor = request.form['autor']
        ano_publicacao = request.form['ano_publicacao']

        cursor.execute("UPDATE LIVRO SET TITULO = ?, autor = ?, ano_publicacao = ? where id_livro = ?",
                       (titulo, autor, ano_publicacao, id))

        con.commit()
        flash("Livro atualizado com sucesso", 'success')
        return redirect(url_for('acervo'))

    cursor.close()
    return render_template('editar.html', livro=livro, titulo='Editar livro')

@app.route('/deletar/<int:id>', methods=['POST'])
def deletar(id):
    cursor = con.cursor() # abre o cursor
    try:
        cursor.execute('DELETE FROM livro WHERE id_livro = ?', (id,))
        con.commit()  # Salva as alterações no banco de dados
        flash('Livro excluído com sucesso!', 'success')  # Mensagem de sucesso
    except Exception as e:
        con.rollback()  # Reverte as alterações em caso de erro
        flash('Erro ao excluir o livro.', 'error')  # Mensagem de erro
    finally:
        cursor.close()  # Fecha o cursor independentemente do resultado
    return redirect(url_for('acervo'))  # Redireciona para a página principal

@app.route('/deletar_usuario/<int:id>', methods=['POST'])
def deletar_usuario(id):
    cursor = con.cursor()
    try:
        cursor.execute('DELETE FROM usuario WHERE id_usuario = ?', (id,))
        con.commit()
        flash('Usuário excluído com sucesso!', 'success')
    except Exception as e:
        con.rollback()
        flash('Erro ao excluir usuário.', 'error')
    finally:
        cursor.close()
    return redirect(url_for('index'))

@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    cursor = con.cursor()
    cursor.execute("SELECT * FROM usuario WHERE id_usuario = ?", (id,))
    usuario = cursor.fetchone()

    if not usuario:
        cursor.close()
        flash("Usuário não encontrado.", 'error')
        return redirect(url_for('index'))
    
    if request.method == "POST":
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        cursor.execute("UPDATE usuario SET nome = ?, email = ?, senha = ? WHERE id_usuario = ?",
                       (nome, email, senha, id))
        
        con.commit()
        flash("Usuário atualizado com sucesso!", 'sucesso')
        return redirect(url_for('index'))
    
    cursor.close()
    return render_template('editar_usuario.html', usuario=usuario, titulo='Editar usuário')

@app.route('/acervo')
def acervo():
    if "id_usuario" not in session:
        flash('Você precisa estar logado para acessar o acervo.', 'error')
        return redirect(url_for('login'))
    cursor = con.cursor()
    cursor.execute("SELECT * FROM LIVRO")
    livros = cursor.fetchall()
    cursor.close()
    return render_template('acervo.html', livros=livros)

@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html')

# usuario
@app.route('/cadastrar_usuario', methods=['POST'])
def cadastrar_usuario():
    nome = request.form['nome']
    email = request.form['email']
    senha = request.form['senha']
    cursor = con.cursor()

    try:
        cursor.execute("SELECT * FROM usuario WHERE email = ?", (email,))
        if cursor.fetchone():
            flash("Usuário já cadastrado!", 'error')
            return redirect(url_for('cadastro.html')) # para o código e dá feedback

        cursor.execute('''INSERT INTO usuario (nome, email, senha)
                                      VALUES (?, ?, ?)''', (nome, email, generate_password_hash(senha).decode('utf-8')))
        con.commit()

        flash("Usuário criado com sucesso!",'success')
        return redirect(url_for('login'))
    except Exception as e:
        flash("Erro ao criar usuário!", 'error')
        return redirect(url_for('cadastrar_usuario'))
    finally:
        cursor.close()

# login
@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop("id_usuario", None)
    flash('Logout feito com sucesso!', 'success')
    return redirect(url_for('index'))

@app.route('/fazer_login/', methods=['POST'])
def fazer_login():
    email = request.form['email']
    senha = request.form['senha']
    cursor = con.cursor()

    try:
        cursor.execute("SELECT id_usuario, nome, email, senha FROM usuario WHERE email = ?", (email,))
        usuario = cursor.fetchone()

        if not usuario:
            flash("Usuário não existe", "error")
            return redirect(url_for('login'))

        if check_password_hash(usuario[3], senha):
            session["id_usuario"] = usuario[0]
            flash("Login feito com sucesso!", "success")
            return redirect(url_for('acervo'))

        flash("Email ou senha incorretos", "error")
    finally:
        cursor.close()
    return redirect(url_for('login'))

@app.route('/gerar', methods=['GET'])
def gerar():
    cursor = con.cursor()
    cursor.execute("SELECT id_livro, titulo, autor, ano_publicacao FROM livro")
    livros = cursor.fetchall()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(200, 10, "Relatorio de Livros", ln=True, align='C')

    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    pdf.set_font("Arial", size=12)

    for livro in livros:
        pdf.cell(200, 10, f"ID: {livro[0]} - {livro[1]} - {livro[2]} - {livro[3]}", ln=True)

    contador_livros = len(livros)
    pdf.ln(10)  # Espaço antes do contador
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, f"Total de livros cadastrados: {contador_livros}", ln=True, align='C')

    pdf_path = "relatorio_livros.pdf"
    pdf.output(pdf_path)
    return send_file(pdf_path, as_attachment=True, mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)