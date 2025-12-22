import { useState, useEffect } from 'react';
import { api } from '../api';
import './Settings.css';

export default function Settings({ isOpen, onClose }) {
  const [availableModels, setAvailableModels] = useState([]);
  const [councilModels, setCouncilModels] = useState([]);
  const [chairmanModel, setChairmanModel] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');
  const [isDarkMode, setIsDarkMode] = useState(() => {
    return document.body.getAttribute('data-theme') === 'dark' || 
           localStorage.getItem('llm-council-theme') === 'dark';
  });

  // Load available models and current config
  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  // Handle dark mode theme
  useEffect(() => {
    if (isDarkMode) {
      document.body.setAttribute('data-theme', 'dark');
      localStorage.setItem('llm-council-theme', 'dark');
    } else {
      document.body.removeAttribute('data-theme');
      localStorage.setItem('llm-council-theme', 'light');
    }
  }, [isDarkMode]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [modelsData, configData] = await Promise.all([
        api.getAvailableModels(),
        api.getConfig(),
      ]);

      setAvailableModels(modelsData.models);
      setCouncilModels(configData.council_models);
      setChairmanModel(configData.chairman_model);
    } catch (err) {
      setError('Failed to load settings: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleModel = (modelId) => {
    if (councilModels.includes(modelId)) {
      // Remove model (but keep at least one)
      if (councilModels.length > 1) {
        setCouncilModels(councilModels.filter((m) => m !== modelId));
      }
    } else {
      // Add model
      setCouncilModels([...councilModels, modelId]);
    }
  };

  const handleSave = async () => {
    if (councilModels.length === 0) {
      setError('Please select at least one council member');
      return;
    }

    if (!chairmanModel) {
      setError('Please select a chairman model');
      return;
    }

    setSaving(true);
    setError(null);
    setSuccessMessage('');

    try {
      await api.updateConfig(councilModels, chairmanModel);

      // Save to localStorage as well for persistence
      localStorage.setItem(
        'llm-council-config',
        JSON.stringify({ councilModels, chairmanModel })
      );

      setSuccessMessage('Configuration saved successfully!');

      // Close modal after a short delay
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (err) {
      setError('Failed to save configuration: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    if (
      confirm(
        'Are you sure you want to reset to default configuration? This will reload the page.'
      )
    ) {
      localStorage.removeItem('llm-council-config');
      window.location.reload();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="settings-overlay" onClick={onClose}>
      <div className="settings-modal" onClick={(e) => e.stopPropagation()}>
        <div className="settings-header">
          <h2>Council Configuration</h2>
          <button className="close-button" onClick={onClose}>
            ×
          </button>
        </div>

        {loading ? (
          <div className="settings-loading">Loading configuration...</div>
        ) : (
          <div className="settings-content">
            {error && <div className="settings-error">{error}</div>}
            {successMessage && (
              <div className="settings-success">{successMessage}</div>
            )}

            <section className="settings-section">
              <h3>Appearance</h3>
              <div className="setting-control">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={isDarkMode}
                    onChange={(e) => setIsDarkMode(e.target.checked)}
                  />
                  Dark Mode
                </label>
              </div>
            </section>

            <section className="settings-section">
              <h3>Council Members</h3>
              <p className="section-description">
                Select which models will participate in Stage 1 and Stage 2.
                Each model will provide its own response and review others.
              </p>

              <div className="model-grid">
                {availableModels.map((model) => (
                  <div
                    key={model.id}
                    className={`model-card ${
                      councilModels.includes(model.id) ? 'selected' : ''
                    }`}
                    onClick={() => handleToggleModel(model.id)}
                  >
                    <div className="model-checkbox">
                      <input
                        type="checkbox"
                        checked={councilModels.includes(model.id)}
                        onChange={() => {}}
                      />
                    </div>
                    <div className="model-info">
                      <div className="model-name">{model.name}</div>
                      <div className="model-provider">{model.provider}</div>
                      <div className="model-description">
                        {model.description}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="selected-count">
                {councilModels.length} model{councilModels.length !== 1 ? 's' : ''} selected
              </div>
            </section>

            <section className="settings-section">
              <h3>Chairman Model</h3>
              <p className="section-description">
                Select which model will synthesize the final answer in Stage 3.
              </p>

              <select
                className="chairman-select"
                value={chairmanModel}
                onChange={(e) => setChairmanModel(e.target.value)}
              >
                <option value="">Select a chairman model...</option>
                {availableModels.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.name} ({model.provider})
                  </option>
                ))}
              </select>
            </section>

            <div className="settings-actions">
              <button
                className="button button-secondary"
                onClick={handleReset}
                disabled={saving}
              >
                Reset to Default
              </button>
              <div className="action-group">
                <button
                  className="button button-tertiary"
                  onClick={onClose}
                  disabled={saving}
                >
                  Cancel
                </button>
                <button
                  className="button button-primary"
                  onClick={handleSave}
                  disabled={saving || councilModels.length === 0 || !chairmanModel}
                >
                  {saving ? 'Saving...' : 'Save Configuration'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
