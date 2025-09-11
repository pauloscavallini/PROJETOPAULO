from flask import Flask, render_template, redirect, request, flash, url_for
import fdb

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
    cursor.execute("SELECT * FROM LIVRO")
    livros = cursor.fetchall()
    cursor.close()
    return render_template('livros.html', livros=livros)

@app.route('/novo')
def novo():
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
            flash('Erro: Livro já cadastrado')
            return redirect(url_for('novo'))

        cursor.execute('''INSERT INTO livro (titulo, autor, ano_publicacao)
                              VALUES (?, ?, ?)''', (titulo, autor, ano_publicacao))
        con.commit()
    finally:
        cursor.close()
    flash("Livro cadastrado com sucesso!")
    return redirect(url_for('index'))


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
        flash("Livro não encontrado")
        return redirect(url_for('index'))

    if request.method == 'POST':
        titulo = request.form['titulo']
        autor = request.form['autor']
        ano_publicacao = request.form['ano_publicacao']

        cursor.execute("UPDATE LIVRO SET TITULO = ?, autor = ?, ano_publicacao = ? where id_livro = ?",
                       (titulo, autor, ano_publicacao, id))

        con.commit()
        flash("Livro atualizado com sucesso")
        return redirect(url_for('index'))

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
    return redirect(url_for('index'))  # Redireciona para a página principal

if __name__ == '__main__':
    app.run(debug=True)