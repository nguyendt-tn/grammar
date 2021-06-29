from flask import request
from application import app
from application import actions

from flask_cors import CORS, cross_origin

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route("/api/v1/grammar/check",methods=['POST'])
@cross_origin()
def grammar():
    user_input = request.form.get('data')
    try:
        prediction = actions.predict(user_input)
        return {"status":200, "prediction": prediction}
    except:
        prediction = actions.predict(user_input)
        return {"status":404, "prediction": prediction}