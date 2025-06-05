import os
from flask import Flask, request, redirect, url_for, render_template, send_from_directory
from werkzeug.utils import secure_filename

import secrets
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, flash, session
from werkzeug.utils import secure_filename
# Assuming utils.py and core.py are in app.deduplicator
from .deduplicator import utils as deduplicator_utils
from .deduplicator import core as deduplicator_core

UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results' # To store processed files or results
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.secret_key = secrets.token_hex(16) # Needed for session and flash messages

# Ensure upload and result directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return redirect(url_for('upload_file'))

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'files[]' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)

        files = request.files.getlist('files[]')
        dedup_type = request.form.get('dedup_type', 'exact')
        try:
            similarity_threshold = float(request.form.get('similarity_threshold', 0.8))
            if not (0.0 <= similarity_threshold <= 1.0):
                flash('Similarity threshold must be between 0.0 and 1.0.', 'error')
                return redirect(request.url)
        except ValueError:
            flash('Invalid similarity threshold.', 'error')
            return redirect(request.url)

        uploaded_filenames = []
        uploaded_file_paths = []

        if not files or all(f.filename == '' for f in files):
            flash('No selected files', 'error')
            return redirect(request.url)

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                uploaded_filenames.append(filename)
                uploaded_file_paths.append(file_path)
            elif file.filename != '': # If filename is not empty but not allowed
                flash(f"File type not allowed for {file.filename}", 'error')

        if not uploaded_filenames:
            # This case means files were selected, but none were of allowed types or other save error
            flash('No valid files were uploaded.', 'error')
            return redirect(request.url)

        # Store file info in session to pass to the results page
        session['uploaded_files_data'] = {
            'filenames': uploaded_filenames,
            'paths': uploaded_file_paths,
            'dedup_type': dedup_type,
            'similarity_threshold': similarity_threshold
        }

        flash(f'{len(uploaded_filenames)} file(s) uploaded successfully. Processing...', 'success')
        return redirect(url_for('process_files_route')) # Corrected redirect

    return render_template('upload.html')

@app.route('/process')
def process_files_route():
    if 'uploaded_files_data' not in session:
        flash('No file data in session. Please upload files first.', 'error')
        return redirect(url_for('upload_file'))

    file_data = session.pop('uploaded_files_data') # Retrieve and clear from session
    texts = []
    parse_errors = []

    for i, file_path in enumerate(file_data['paths']):
        parsed_text = deduplicator_utils.parse_file(file_path)
        if parsed_text.startswith("Error:"):
            parse_errors.append(f"Could not parse {file_data['filenames'][i]}: {parsed_text}")
        else:
            texts.append(parsed_text)

    if parse_errors:
        for error in parse_errors:
            flash(error, 'error')
        # Decide if you want to stop or proceed with partially parsed texts
        # For now, let's redirect to results page to show these errors
        session['results_data'] = {'error': '<br>'.join(parse_errors), 'session_files': file_data['filenames']}
        return redirect(url_for('results_page'))

    if not texts:
        flash('No text could be extracted from the uploaded files.', 'error')
        session['results_data'] = {'error': 'No text could be extracted.', 'session_files': file_data['filenames']}
        return redirect(url_for('results_page'))

    results_data = {'session_files': file_data['filenames']}
    if file_data['dedup_type'] == 'exact':
        # Exact duplicates will be handled by identifying groups of identical texts
        duplicate_groups = deduplicator_core.find_exact_duplicates(texts)
        results_data['duplicate_groups'] = duplicate_groups
        # For exact, "unique files" could be those not in any duplicate group
        all_duplicate_indices = {idx for group in duplicate_groups for idx in group}
        unique_indices = [i for i, _ in enumerate(texts) if i not in all_duplicate_indices]
        results_data['unique_files'] = [file_data['filenames'][i] for i in unique_indices]

    elif file_data['dedup_type'] == 'near':
        duplicate_groups = deduplicator_core.find_near_duplicates(texts, file_data['similarity_threshold'])
        results_data['duplicate_groups'] = duplicate_groups
        all_duplicate_indices = {idx for group in duplicate_groups for idx in group}
        unique_indices = [i for i, _ in enumerate(texts) if i not in all_duplicate_indices]
        results_data['unique_files'] = [file_data['filenames'][i] for i in unique_indices]

    session['results_data'] = results_data
    return redirect(url_for('results_page'))

@app.route('/results')
def results_page():
    results = session.pop('results_data', None) # Get results and remove from session
    if not results:
        flash('No results to display or results have expired. Please upload files again.', 'warning')
        return redirect(url_for('upload_file'))

    # `session_files` should be passed to the template for displaying filenames
    return render_template('results.html', **results)


if __name__ == '__main__':
    app.run(debug=True)
