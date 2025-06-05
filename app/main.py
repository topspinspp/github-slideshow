import os
import secrets
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, flash, session, jsonify, send_file
from werkzeug.utils import secure_filename
import pandas as pd
import zipfile
import io

# Assuming utils.py and core.py are in app.deduplicator
from .deduplicator import utils as deduplicator_utils
from .deduplicator import core as deduplicator_core

UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'txt', 'csv', 'xls', 'xlsx'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.secret_key = secrets.token_hex(16)

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

        sheet_name_str = request.form.get('sheet_name', '0')
        columns_to_use_str = request.form.get('columns_to_use', '')

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
            elif file.filename != '':
                flash(f"File type not allowed for {file.filename}", 'error')

        if not uploaded_filenames:
            flash('No valid files were uploaded.', 'error')
            return redirect(request.url)

        session['uploaded_files_data'] = {
            'filenames': uploaded_filenames,
            'paths': uploaded_file_paths,
            'dedup_type': dedup_type,
            'similarity_threshold': similarity_threshold,
            'sheet_name': sheet_name_str,
            'columns_to_use_str': columns_to_use_str
        }

        flash(f'{len(uploaded_filenames)} file(s) uploaded successfully. Processing...', 'success')
        return redirect(url_for('process_files_route'))

    return render_template('upload.html')

@app.route('/get-file-columns', methods=['POST'])
def get_file_columns():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    temp_file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_header_check_{filename}")

    try:
        file.save(temp_file_path)
        file_ext = os.path.splitext(filename)[1].lower()
        df = None

        if file_ext == '.csv':
            try:
                df = pd.read_csv(temp_file_path, encoding='utf-8', nrows=0)
            except UnicodeDecodeError:
                df = pd.read_csv(temp_file_path, encoding='gbk', nrows=0)
        elif file_ext in ['.xls', '.xlsx']:
            sheet_name_form = request.form.get('sheet_name', '0')
            try:
                sheet_name = int(sheet_name_form)
            except ValueError:
                sheet_name = sheet_name_form
            df = pd.read_excel(temp_file_path, sheet_name=sheet_name, nrows=0, engine='openpyxl')
        else:
            return jsonify({"error": "Unsupported file type for column extraction."}), 400

        if df is not None:
            return jsonify({"columns": list(df.columns)})
        else:
            return jsonify({"error": "Could not determine columns for the given file type."}), 400

    except Exception as e:
        app.logger.error(f"Error in /get-file-columns for file {filename}: {e}")
        return jsonify({"error": "Could not read columns from file. Please ensure it is a valid CSV/Excel file."}), 500
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.route('/process')
def process_files_route():
    if 'uploaded_files_data' not in session:
        flash('No file data in session. Please upload files first.', 'error')
        return redirect(url_for('upload_file'))

    file_data = session.pop('uploaded_files_data')

    sheet_name_param = file_data.get('sheet_name', '0')
    try:
        sheet_name_param = int(sheet_name_param)
    except ValueError:
        pass

    columns_to_use_str = file_data.get('columns_to_use_str', '')
    if columns_to_use_str:
        columns_to_use_param = [col.strip() for col in columns_to_use_str.split(',') if col.strip()]
    else:
        columns_to_use_param = None

    texts = []
    parse_errors = []

    for i, file_path in enumerate(file_data['paths']):
        parsed_lines = deduplicator_utils.parse_file(
            file_path,
            sheet_name=sheet_name_param,
            columns_to_use=columns_to_use_param
        )

        if parsed_lines and isinstance(parsed_lines, list) and parsed_lines[0].startswith("Error:"):
            parse_errors.append(f"Could not parse {file_data['filenames'][i]}: {parsed_lines[0]}")
        elif not parsed_lines:
            texts.append("")
        else:
            full_text_content = "\n".join(parsed_lines)
            texts.append(full_text_content)

    if parse_errors:
        for error in parse_errors:
            flash(error, 'error')
        if not texts and parse_errors:
             session['results_data'] = {'error': '<br>'.join(parse_errors), 'session_files': file_data['filenames']}
             return redirect(url_for('results_page'))

    if not texts and not parse_errors:
        flash('No text could be extracted from the uploaded files, or all files were empty.', 'error')
        session['results_data'] = {'error': 'No text could be extracted or all files were empty.', 'session_files': file_data['filenames']}
        return redirect(url_for('results_page'))

    results_data = {'session_files': file_data['filenames']}
    if file_data['dedup_type'] == 'exact':
        duplicate_groups = deduplicator_core.find_exact_duplicates(texts)
        results_data['duplicate_groups'] = duplicate_groups
        all_duplicate_indices = {idx for group in duplicate_groups for idx in group}
        unique_indices = [i for i, _ in enumerate(texts) if i not in all_duplicate_indices]
        results_data['unique_files'] = [file_data['filenames'][i] for i in unique_indices]

    elif file_data['dedup_type'] == 'near':
        duplicate_groups = deduplicator_core.find_near_duplicates(texts, file_data['similarity_threshold'])
        results_data['duplicate_groups'] = duplicate_groups
        all_duplicate_indices = {idx for group in duplicate_groups for idx in group}
        unique_indices = [i for i, _ in enumerate(texts) if i not in all_duplicate_indices]
        results_data['unique_files'] = [file_data['filenames'][i] for i in unique_indices]

    session['results_data'] = results_data # Save results for the results page first

    # Logic for preparing downloadable files
    downloadable_file_paths = []
    # Original file paths are in file_data['paths']
    # results_data['unique_files'] contains filenames, not indices directly to file_data['paths']
    # results_data['duplicate_groups'] contains indices relative to 'texts' list.
    # We need a mapping from filename in texts back to its original path.

    # Create a list of unique file paths based on the unique_files list (which contains filenames)
    if 'unique_files' in results_data and results_data['unique_files']:
        for i, fname_in_all_uploaded in enumerate(file_data['filenames']):
            if fname_in_all_uploaded in results_data['unique_files']:
                 if i < len(file_data['paths']): # Boundary check
                    downloadable_file_paths.append(file_data['paths'][i])

    # Add one representative from each duplicate group
    if 'duplicate_groups' in results_data and results_data['duplicate_groups']:
        for group_indices_in_texts in results_data['duplicate_groups']:
            if group_indices_in_texts: # If group is not empty
                # This index is relative to the 'texts' list processed.
                # We need to find which original file this corresponds to.
                # The 'texts' list is in the same order as file_data['paths'] and file_data['filenames']
                first_file_idx_in_texts = group_indices_in_texts[0]
                if first_file_idx_in_texts < len(file_data['paths']): # Boundary check
                    representative_path = file_data['paths'][first_file_idx_in_texts]
                    if representative_path not in downloadable_file_paths:
                        downloadable_file_paths.append(representative_path)

    if downloadable_file_paths:
        session['downloadable_files_paths'] = downloadable_file_paths
        session['show_download_button'] = True
    else:
        session['show_download_button'] = False # Ensure it's False if no files

    return redirect(url_for('results_page'))

@app.route('/download-zip')
def download_zip():
    if 'downloadable_files_paths' not in session or not session['downloadable_files_paths']:
        flash('No files available for download or session expired.', 'error')
        return redirect(url_for('upload_file'))

    paths = session.pop('downloadable_files_paths', [])
    # Keep 'show_download_button' in session until results page is reloaded or new process starts
    # session.pop('show_download_button', False)

    if not paths:
        flash('No file paths found for download.', 'error')
        return redirect(url_for('upload_file'))

    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in paths:
            if os.path.exists(file_path):
                zf.write(file_path, arcname=os.path.basename(file_path))
            else:
                app.logger.warning(f"File not found for zipping: {file_path}")
                flash(f"Warning: File {os.path.basename(file_path)} was not found and not included in ZIP.", "warning")

    memory_file.seek(0)

    if not memory_file.getbuffer().nbytes:
        flash('Could not create ZIP file as no valid files were found to include.', 'error')
        # Redirect to results page, as results_data might still be there if download failed post-processing
        return redirect(url_for('results_page'))

    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name='deduplicated_files.zip'
    )

@app.route('/results')
def results_page():
    results = session.get('results_data', None) # Use get to not pop it immediately
    # show_download_button = session.get('show_download_button', False) # Get button status

    if not results: # If no results, redirect to upload
        flash('No results to display or results have expired. Please upload files again.', 'warning')
        return redirect(url_for('upload_file'))

    # To ensure results are shown only once with their download button, then cleared
    # Or manage session data more carefully if user can refresh results page.
    # For now, let's pop results_data after retrieving for display,
    # but 'show_download_button' and 'downloadable_files_paths' persist until download/new upload.
    # A better approach might be to pass a job_id and retrieve results.

    # If we want to clear results_data after displaying it once:
    # final_results_to_display = session.pop('results_data', {})
    # But this means if they refresh, it's gone.
    # For now, let results persist with download button until next upload cycle clears session['uploaded_files_data']

    return render_template('results.html', **results) # show_download_button=show_download_button will be passed via session access in template

if __name__ == '__main__':
    app.run(debug=True)
