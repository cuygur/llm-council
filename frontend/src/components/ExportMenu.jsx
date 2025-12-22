import { useState } from 'react';
import { api } from '../api';
import './ExportMenu.css';

export default function ExportMenu({ conversationId, conversationTitle, onClose }) {
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState(null);

  const handleExport = async (format) => {
    setExporting(true);
    setError(null);

    try {
      // Build the export URL
      const url = `http://localhost:8001/api/conversations/${conversationId}/export?format=${format}`;

      // Create a temporary link and trigger download
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error('Export failed');
      }

      // Get the filename from Content-Disposition header or use default
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `${conversationTitle || 'conversation'}.${format}`;

      if (contentDisposition) {
        const matches = /filename="?([^"]+)"?/.exec(contentDisposition);
        if (matches && matches[1]) {
          filename = matches[1];
        }
      }

      // Create blob and download
      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);

      // Close menu after successful export
      setTimeout(() => {
        onClose();
      }, 500);
    } catch (err) {
      setError('Failed to export: ' + err.message);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="export-menu-overlay" onClick={onClose}>
      <div className="export-menu" onClick={(e) => e.stopPropagation()}>
        <div className="export-menu-header">
          <h3>Export Conversation</h3>
          <button className="close-btn" onClick={onClose}>
            ×
          </button>
        </div>

        {error && <div className="export-error">{error}</div>}

        <div className="export-options">
          <button
            className="export-option"
            onClick={() => handleExport('markdown')}
            disabled={exporting}
          >
            <div className="export-icon">📝</div>
            <div className="export-info">
              <div className="export-title">Markdown</div>
              <div className="export-desc">
                Plain text with formatting, great for documentation
              </div>
            </div>
          </button>

          <button
            className="export-option"
            onClick={() => handleExport('json')}
            disabled={exporting}
          >
            <div className="export-icon">📊</div>
            <div className="export-info">
              <div className="export-title">JSON</div>
              <div className="export-desc">
                Structured data for analysis and processing
              </div>
            </div>
          </button>

          <button
            className="export-option"
            onClick={() => handleExport('html')}
            disabled={exporting}
          >
            <div className="export-icon">🌐</div>
            <div className="export-info">
              <div className="export-title">HTML</div>
              <div className="export-desc">
                Styled webpage, can be converted to PDF
              </div>
            </div>
          </button>
        </div>

        {exporting && (
          <div className="export-loading">Exporting conversation...</div>
        )}
      </div>
    </div>
  );
}
