from flask import flash, render_template, request, redirect, url_for, send_from_directory, send_file
from app import app, db, forms, models
from werkzeug import secure_filename
import io
import uuid
import os
import datetime

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")

@app.route('/Upload', methods=['POST','GET'])
def upload():
    filenames = ''
    if request.method == 'POST':
        filenames = []
        uploaded_files = request.files.getlist("file[]")
        for file in uploaded_files:
            if file and allowed_file(file.filename):
                id = str(uuid.uuid4())
                uploadDate = datetime.datetime.now()
                fileName = secure_filename(file.filename)
                fileType = fileName.rsplit('.', 1)[1]
                file.seek(0, os.SEEK_END)
                fileSize = file.tell()
                fileText = file.stream.getvalue()
                memo = models.Memoranda(id=id, date=uploadDate, fileName=fileName, fileType=fileType, file=fileText, fileSize=fileSize)
                db.session.add(memo)
                db.session.commit()
                filenames.append(fileName)
                file.close()    
    memos = models.Memoranda.query.order_by(models.Memoranda.date.desc()).all()
    
    return render_template('upload.html',
        title = 'Upload',
        filenames=filenames,
        memos=memos)
