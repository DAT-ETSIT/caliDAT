from flask import Flask, render_template, request, redirect, url_for, send_from_directory
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


@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

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

if __name__ == '__main__':
    app.run(debug=True)
