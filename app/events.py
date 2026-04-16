from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from app.logic import get_directions, get_options

bp = Blueprint('events', __name__)

@bp.route('/', methods=['GET'])
@login_required
def index():
    entrances, classrooms = get_options()
    return render_template('index.html', entranceOptions=entrances, classroomOptions=classrooms)

@bp.route('/directions', methods=['POST'])
@login_required
def directions():
    steps = None
    coordinates = None
    error = None
    entrance = request.form.get('entrance')
    classroom = request.form.get('classroom')
    if not entrance or not classroom:
        error = 'Missing entrance or classroom parameter'
    else:
        try:
            result = get_directions(entrance, classroom)
            if isinstance(result, str):
                error = 'No route could be found between the selected entrance and destination. Please check your selections and try again.'
            else:
                steps = result["directions"]
                coordinates = result["coordinates"]
        except RuntimeError as e:
            error = str(e)
    entrances, classrooms = get_options()
    return render_template('index.html', steps=steps, coordinates=coordinates, error=error,
                           entranceOptions=entrances, classroomOptions=classrooms)

@bp.route('/api/test')
def test():
    directions = get_directions("NPB_5_E1", "NPB_5_154")
    return jsonify(directions)
