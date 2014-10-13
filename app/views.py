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
                memo = models.Memoranda(id=id, date=uploadDate, fileName=fileName, fileType=fileType, file=fileText, fileSize=fileSize, fileMap_id = "")
                db.session.add(memo)
                db.session.commit()
                filenames.append(fileName)
                file.close()    
    memos = models.Memoranda.query.order_by(models.Memoranda.date.desc()).all()
    
    return render_template('upload.html',
        title = 'Upload',
        filenames=filenames,
        memos=memos)


@app.route('/FileMaps', methods=['POST','GET'])
def filemaps():
    form = forms.NewFileMap()
    if request.method == 'POST':
      id = str(uuid.uuid4())
      fileMapName = form.fileMapName.data
      fileMap = models.FileMaps(id=id, fileMapName=fileMapName)
      db.session.add(fileMap)
      db.session.commit()
    fileMaps = models.FileMaps.query.order_by(models.FileMaps.fileMapName.desc()).all()
    return render_template('filemaps.html', 
      fileMaps=fileMaps,
      form=form)

@app.route('/FileMaps/delete/<fileMapName>')
def deletefilemap(fileMapName):
    fileMap = models.FileMaps.query.filter_by(fileMapName=fileMapName).first()
    db.session.delete(fileMap)
    db.session.commit()
    fileMaps = models.FileMaps.query.order_by(models.FileMaps.fileMapName.desc()).all()
    form = forms.NewFileMapping()
    return redirect(url_for('filemaps'))


@app.route('/FileMaps/<fileMapName>', methods=['POST','GET'])
def filemap(fileMapName):
    form = forms.NewFileMapping()
    fileMap = models.FileMaps.query.filter_by(fileMapName=fileMapName).first()
    fileMapID = fileMap.id
    fileMappings = models.FileMappings.query.filter_by(fileMap_id=fileMapID).all()
    if request.method == 'POST':
      id = str(uuid.uuid4())
      fileMappingName = form.fileMappingName.data
      fileMappingType = form.fileMappingType.data
      fileMappingArgument = form.fileMappingArgument.data
      fileMappingValue = form.fileMappingValue.data
      fileMappingEntry = models.FileMappings(id=id, fileMap_id=fileMapID, fileMappingName=fileMappingName, fileMapping={"idtype":fileMappingType,"argument":fileMappingArgument, "value":fileMappingValue})
      db.session.add(fileMappingEntry)
      db.session.commit()
      return redirect(url_for('filemap', fileMapName = fileMap.fileMapName))
    return render_template('filemap.html', fileMappings=fileMappings, fileMapName=fileMapName, form=form)

@app.route('/FileMaps/delete/<fileMapName>/<fileMappingName>')
def deletefilemapping(fileMapName, fileMappingName):
  fileMap = models.FileMaps.query.filter_by(fileMapName=fileMapName).first()
  fileMapID = fileMap.id
  fileMapping = models.FileMappings.query.filter_by(fileMappingName=fileMappingName, fileMap_id=fileMapID).first()
  db.session.delete(fileMapping)
  db.session.commit()
  return redirect(url_for('filemap', fileMapName = fileMap.fileMapName))
