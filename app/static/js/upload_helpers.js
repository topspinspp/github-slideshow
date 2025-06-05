document.addEventListener('DOMContentLoaded', function () {
    const fileInput = document.getElementById('files');
    const sheetNameGroup = document.getElementById('sheetNameGroup');
    const columnSelectGroup = document.getElementById('columnSelectGroup');
    const columnCheckboxesDiv = document.getElementById('columnCheckboxes');
    const columnsToUseHiddenInput = document.getElementById('columns_to_use');
    const columnLoadingDiv = document.getElementById('columnLoading');
    const columnErrorDiv = document.getElementById('columnError');

    fileInput.addEventListener('change', handleFileSelect);

    function handleFileSelect(event) {
        // Reset and hide groups initially
        sheetNameGroup.style.display = 'none';
        columnSelectGroup.style.display = 'none';
        columnCheckboxesDiv.innerHTML = ''; // Clear previous checkboxes
        columnsToUseHiddenInput.value = '';
        columnErrorDiv.style.display = 'none';
        columnErrorDiv.textContent = '';

        if (event.target.files.length === 0) {
            return; // No file selected
        }

        const file = event.target.files[0]; // Process only the first file for column selection UI
        const fileName = file.name.toLowerCase();

        if (fileName.endsWith('.xls') || fileName.endsWith('.xlsx')) {
            sheetNameGroup.style.display = 'block';
            columnSelectGroup.style.display = 'block';
            fetchColumns(file);
        } else if (fileName.endsWith('.csv')) {
            sheetNameGroup.style.display = 'none'; // No sheet name for CSV
            columnSelectGroup.style.display = 'block';
            fetchColumns(file);
        } else if (fileName.endsWith('.txt')) {
            // For TXT files, no columns or sheet name needed
            sheetNameGroup.style.display = 'none';
            columnSelectGroup.style.display = 'none';
        }
    }

    function fetchColumns(file) {
        columnLoadingDiv.style.display = 'block';
        columnCheckboxesDiv.innerHTML = ''; // Clear previous
        columnErrorDiv.style.display = 'none';


        const formData = new FormData();
        formData.append('file', file);

        // Get sheet name if visible and has value for Excel files
        const sheetNameInput = document.getElementById('sheet_name');
        if (sheetNameGroup.style.display === 'block' && sheetNameInput.value.trim() !== '') {
            formData.append('sheet_name', sheetNameInput.value.trim());
        }

        fetch('/get-file-columns', { // This endpoint will be created in the next step
            method: 'POST',
            body: formData,
        })
        .then(response => {
            columnLoadingDiv.style.display = 'none';
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error || 'Server error'); });
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                columnErrorDiv.textContent = 'Error fetching columns: ' + data.error;
                columnErrorDiv.style.display = 'block';
            } else if (data.columns && data.columns.length > 0) {
                populateColumnCheckboxes(data.columns);
            } else {
                columnErrorDiv.textContent = 'No columns found or file is empty.';
                columnErrorDiv.style.display = 'block';
            }
        })
        .catch(error => {
            columnLoadingDiv.style.display = 'none';
            columnErrorDiv.textContent = 'Error fetching columns: ' + error.message;
            columnErrorDiv.style.display = 'block';
            console.error('Error fetching columns:', error);
        });
    }

    function populateColumnCheckboxes(columns) {
        columns.forEach(column => {
            const label = document.createElement('label');
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.name = 'column_checkbox'; // Not directly submitted, used for JS
            checkbox.value = column;
            checkbox.addEventListener('change', updateSelectedColumnsHiddenInput);

            label.appendChild(checkbox);
            label.appendChild(document.createTextNode(column));
            columnCheckboxesDiv.appendChild(label);
            columnCheckboxesDiv.appendChild(document.createElement('br'));
        });
    }

    function updateSelectedColumnsHiddenInput() {
        const selectedColumns = [];
        document.querySelectorAll('input[name="column_checkbox"]:checked').forEach(checkbox => {
            selectedColumns.push(checkbox.value);
        });
        columnsToUseHiddenInput.value = selectedColumns.join(',');
    }

    // Add event listener for sheet_name input to re-fetch columns if it changes for Excel
    const sheetNameInput = document.getElementById('sheet_name');
    sheetNameInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];
            const fileName = file.name.toLowerCase();
            if (fileName.endsWith('.xls') || fileName.endsWith('.xlsx')) {
                 columnErrorDiv.style.display = 'none'; // Clear previous error
                 fetchColumns(file); // Re-fetch columns if sheet name changes
            }
        }
    });
});
