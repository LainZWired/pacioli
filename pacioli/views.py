from flask import flash, render_template, request, redirect, url_for, send_from_directory, send_file
from pacioli import app, db, forms, models
import io
import uuid
import os
import datetime
import pacioli.memoranda


@app.route('/')
def index():
  return render_template("index.html")

@app.route('/Upload', methods=['POST','GET'])
def upload():
  filenames = ''
  if request.method == 'POST':
    uploaded_files = request.files.getlist("file[]")
    for file in uploaded_files:
      pacioli.memoranda.process(file)
    return redirect(url_for('upload'))
  memos = models.Memoranda.query.order_by(models.Memoranda.date.desc()).all()
  
  return render_template('upload.html',
    title = 'Upload',
    memos=memos)

@app.route('/Memoranda', methods=['POST','GET'])
def memoranda():
  memos = models.Memoranda.query.order_by(models.Memoranda.date.desc()).all()
  return render_template('memoranda.html',
    title = 'Memoranda',
    memos=memos)
    
@app.route('/Memoranda/Delete/<fileName>')
def delete_memoranda(fileName):
  memo = models.Memoranda.query.filter_by(fileName=fileName).first()
  db.session.delete(memo)
  db.session.commit()
  return redirect(url_for('memoranda'))
