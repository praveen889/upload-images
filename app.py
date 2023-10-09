from flask import Flask, render_template, request, abort, make_response, jsonify
from werkzeug.utils import secure_filename
from goolge.cloud import firestore, storage
from decouple import config

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'static/'

GOOGLE_CLOUD_STORAGE_API_KEY = config('GOOGLE_CLOUD_STORAGE_API_KEY')
GOOGLE_FIRESTORE_API_KEY = config('GOOGLE_FIRESTORE_API_KEY')

db = firestore.Client(api_key=GOOGLE_FIRESTORE_API_KEY)

storage_client = storage.Client(credentials=GOOGLE_CLOUD_STORAGE_API_KEY)
bucket_name = 'images'


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/',methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST' and 'file' in request.files:
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(filename)
            blob.upload_from_string(file.read())

            image_data = {
                'filename': filename,
                'location': f'gs://{bucket_name}/{filename}',
                'size': blob.size
            }
            db.collection('images').add(image_data)

            images = [blob.name for blob in bucket.list_blobs()]
            return render_template('index.html', images=images)

    
    images = [] 
    return render_template('index.html', images=images)

@app.errorhandler(413)
def too_large(e):
    return make_response(jsonify(message="File is too large"), 413)

if __name__ == '__main__':
    app.run(debug=True)