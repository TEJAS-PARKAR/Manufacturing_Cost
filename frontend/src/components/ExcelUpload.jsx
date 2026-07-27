import { useRef, useState } from 'react';

export default function ExcelUpload({ onProcess, loading }) {
  const fileInputRef = useRef(null);
  const [file, setFile] = useState(null);

  const handleFileChange = (e) => {
    const selected = e.target.files?.[0];
    if (selected) setFile(selected);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) setFile(dropped);
  };

  const handleProcess = () => {
    if (file) onProcess(file);
  };

  return (
    <div>
      <h3 className="section-heading">Upload Costing Excel Sheet</h3>

      <div
        className={`upload-area${file ? ' has-file' : ''}`}
        onClick={() => fileInputRef.current?.click()}
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".xlsx,.xls"
          onChange={handleFileChange}
        />
        <div className="upload-icon">📄</div>
        {file ? (
          <div className="file-name">{file.name}</div>
        ) : (
          <div className="upload-text">
            Click or drag &amp; drop your Excel file here (.xlsx, .xls)
          </div>
        )}
      </div>

      {file && (
        <div className="alert alert-info" style={{ marginBottom: '0.8rem' }}>
          File ready: <strong>{file.name}</strong>
        </div>
      )}

      <button
        className="btn-primary"
        onClick={handleProcess}
        disabled={!file || loading}
      >
        {loading ? (
          <span className="spinner-overlay">
            <span className="spinner" />
            Extracting data from Excel sheet…
          </span>
        ) : (
          'Process Excel Sheet'
        )}
      </button>
    </div>
  );
}
