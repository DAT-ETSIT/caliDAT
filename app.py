from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

app = Flask(__name__)

app.template_folder = './templates'


# Función para cargar los datos JSON de una asignatura específica
def load_subject_data(year, degree):
    data_path = os.path.join('data', year, degree + '.json')
    if os.path.exists(data_path):
        with open(data_path, 'r') as f:
            data = json.load(f)
        return data
    else:
        return None

# Función para generar los gráficos de pie
def generate_pie_charts(ratings_data):
    charts = {}
    for metric in ['performance', 'success', 'abandonment']:
        enrolled = int(ratings_data[metric]['enrolled'])
        passed = int(ratings_data[metric]['pass'])
        if enrolled > 0:
            rate_percentage = passed / enrolled * 100
        else:
            rate_percentage = 0
        labels = ['Aprobados', 'Suspensos']
        values = [passed, enrolled - passed]
        fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
        if fig.data:
            # Asegurarse de que colors esté inicializado
            if not fig.data[0].marker.colors:
                fig.data[0].marker.colors = ['green', 'red']
            else:
                # Añadir identificador único a cada "slice" solo si hay datos
                for i, label in enumerate(labels):
                    fig.data[0].marker.colors[i] = 'red' if label == 'Suspensos' else 'green'
        fig.update_traces(hoverinfo='label+percent+value')
        charts[metric] = fig.to_html(full_html=False)
    return charts


@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Ruta principal para seleccionar la carpeta de la que se importarán los archivos JSON
@app.route('/', methods=['GET'])
def select_year():
    folders = os.listdir('./data')
    return render_template('select_year.html', folders=folders)

# Ruta para mostrar la lista de archivos disponibles en una carpeta específica
@app.route('/<year>', methods=['GET'])
def select_degree(year):
    folder_path = f'./data/{year}'
    if os.path.isdir(folder_path):
        files = os.listdir(folder_path)
        # Remover la extensión .json de los nombres de archivo
        files_without_extension = [file.split('.')[0] for file in files if file.endswith('.json')]
        return render_template('select_degree.html', year=year, files=files_without_extension)
    else:
        return f"Error: La carpeta {year} no existe."


# Ruta para visualizar datos de una asignatura específica
@app.route('/<year>/<degree>', methods=['GET', 'POST'])
def visualize_data(year, degree):
    if request.method == 'POST':
        subject_code = request.form['subject']
        return redirect(url_for('visualize_data', year=year, degree=degree, subject_code=subject_code))

    subject_code = request.args.get('subject_code', None)
    data = load_subject_data(year, degree)
    if data:
        if subject_code:
            for subject in data:
                if subject['subject_code'] == subject_code:
                    subject_data = subject
                    pie_charts = generate_pie_charts(subject_data['reports_info'][0]['ratings_data'])
                    return render_template('visualize_subject.html', subject_data=subject_data, pie_charts=pie_charts)
        else:
            return render_template('select_subject.html', data=data)

    return "Archivo no encontrado"

@app.route('/<year>/<degree>/select_multiple_subjects', methods=['GET'])
def select_multiple_subjects(year, degree):
    # Encuentra la ruta del archivo JSON de las asignaturas
    filename = f"./data/{year}/{degree}.json"
    if os.path.exists(filename):
        # Carga los datos del archivo JSON
        with open(filename, 'r') as file:
            subjects = json.load(file)
        return render_template('select_multiple_subjects.html', year=year, degree=degree, subjects=subjects)
    else:
        return "Error: El archivo de datos no existe."

@app.route('/<year>/<degree>/visualize_multiple_subjects', methods=['GET'])
def visualize_multiple_subjects(year, degree):
    if request.method == 'GET':
        selected_subjects = request.args.getlist('asignaturas')  # Obtiene las asignaturas seleccionadas
        
        # Encuentra la ruta del archivo JSON de todas las asignaturas
        filename = f"./data/{year}/{degree}.json"
        if os.path.exists(filename):
            # Carga los datos del archivo JSON
            with open(filename, 'r') as file:
                all_subjects_data = json.load(file)
                
            # Filtra las asignaturas seleccionadas
            selected_subjects_data = [subject for subject in all_subjects_data if subject['subject_code'] in selected_subjects]
            
            # Genera los gráficos de tarta para cada asignatura seleccionada
            pie_charts = {}
            for subject_data in selected_subjects_data:
                pie_charts[subject_data['subject_code']] = generate_pie_charts(subject_data['reports_info'][0]['ratings_data'])
            
            # Renderiza la plantilla visualize_multiple_subjects.html para mostrar los datos de las asignaturas seleccionadas
            return render_template('visualize_multiple_subjects.html', subjects_data=selected_subjects_data, pie_charts=pie_charts)
        else:
            return "Error: El archivo de datos no existe."
    else:
        return "Error: Método POST no permitido en esta ruta."




if __name__ == '__main__':
    app.run(debug=True)
