from flask import Flask, render_template, request, redirect, url_for
import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

app = Flask(__name__)

app.template_folder = './templates'


# Función para cargar los datos JSON de una asignatura específica
def load_subject_data(year, term):
    data_path = os.path.join('data', year, term + '.json')
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




# Ruta para visualizar datos de una asignatura específica
@app.route('/<year>/<term>', methods=['GET', 'POST'])
def visualize_data(year, term):
    if request.method == 'POST':
        subject_code = request.form['subject']
        return redirect(url_for('visualize_data', year=year, term=term, subject_code=subject_code))

    subject_code = request.args.get('subject_code', None)
    data = load_subject_data(year, term)
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

# Ruta para visualizar datos de asignaturas agrupadas
@app.route('/grouped')
def visualize_grouped_data():
    selected_subjects = request.args.getlist('subject')
    all_data = {}
    for year_folder in os.listdir('data'):
        year_path = os.path.join('data', year_folder)
        if os.path.isdir(year_path):
            for json_file in os.listdir(year_path):
                if json_file.endswith('.json'):
                    with open(os.path.join(year_path, json_file), 'r') as f:
                        data = json.load(f)
                    for subject in data:
                        subject_code = subject['subject_code']
                        if subject_code in selected_subjects:
                            if subject_code not in all_data:
                                all_data[subject_code] = []
                            all_data[subject_code].append({
                                'year': year_folder,
                                'term': json_file.split('.')[0],
                                'ratings_data': subject['reports_info'][0]['ratings_data']
                            })

    # Procesamiento de datos para agrupación
    grouped_data = {}
    for subject_code, data in all_data.items():
        df = pd.DataFrame(data)
        grouped_data[subject_code] = df.groupby(['year', 'term']).mean().reset_index()

    # Renderizar plantilla HTML con datos agrupados
    return render_template('grouped_visualize.html', grouped_data=grouped_data)

if __name__ == '__main__':
    app.run(debug=True)
