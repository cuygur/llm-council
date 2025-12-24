import { useState, useEffect } from 'react';
import { api } from '../api';
import './Settings.css';

export default function Settings({ 

  isOpen, 

  onClose, 

  onSaveOverride, 

  title = "Council Configuration",

  saveButtonText = "Save Configuration" 

}) {

  const [availableModels, setAvailableModels] = useState([]);

  const [councilModels, setCouncilModels] = useState([]);

    const [chairmanModel, setChairmanModel] = useState('');

    const [modelPersonas, setModelPersonas] = useState({});

    const [loading, setLoading] = useState(true);

    const [saving, setSaving] = useState(false);

  const [error, setError] = useState(null);

  const [successMessage, setSuccessMessage] = useState('');
  const [presets, setPresets] = useState([]);
  const [newPresetName, setNewPresetName] = useState('');
  const [modelSearch, setModelSearch] = useState('');

  const [isDarkMode, setIsDarkMode] = useState(() => {

    return document.body.getAttribute('data-theme') === 'dark' || 

           localStorage.getItem('llm-council-theme') === 'dark';

  });



  // Load available models and current config

  useEffect(() => {

    if (isOpen) {

      loadData();

      loadPresets();

    }

  }, [isOpen]);



  const loadPresets = () => {

    const savedPresets = localStorage.getItem('llm-council-presets');

    if (savedPresets) {

      setPresets(JSON.parse(savedPresets));

    } else {

      // Default presets

      const defaultPresets = [

        {

          name: 'The Big Three',

          councilModels: ['openai/gpt-4o', 'anthropic/claude-3-5-sonnet', 'google/gemini-1.5-pro'],

          chairmanModel: 'google/gemini-1.5-pro'

        },

        {

          name: 'Fast & Cheap',

          councilModels: ['openai/gpt-4o-mini', 'anthropic/claude-3-haiku', 'google/gemini-1.5-flash'],

          chairmanModel: 'google/gemini-1.5-flash'

        }

      ];

      setPresets(defaultPresets);

      localStorage.setItem('llm-council-presets', JSON.stringify(defaultPresets));

    }

  };



  const handleApplyPreset = (preset) => {

    setCouncilModels(preset.councilModels);

    setChairmanModel(preset.chairmanModel);

  };



  const handleSavePreset = () => {

    if (!newPresetName.trim()) return;

    const newPreset = {

      name: newPresetName,

      councilModels,

      chairmanModel

    };

    const updatedPresets = [...presets, newPreset];

    setPresets(updatedPresets);

    localStorage.setItem('llm-council-presets', JSON.stringify(updatedPresets));

    setNewPresetName('');

  };



  const handleDeletePreset = (index) => {

    const updatedPresets = presets.filter((_, i) => i !== index);

    setPresets(updatedPresets);

    localStorage.setItem('llm-council-presets', JSON.stringify(updatedPresets));

  };



  const loadData = async () => {

    setLoading(true);

    setError(null);

    try {

      const [modelsData, configData] = await Promise.all([

        api.getAvailableModels(),

        api.getConfig(),

      ]);



      setAvailableModels(modelsData.models);

      

      // If we are starting a new conversation, we might want to default to the current config

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



        if (onSaveOverride) {



          await onSaveOverride(councilModels, chairmanModel, modelPersonas);



          return;



        }



  



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

          <h2>{title}</h2>

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



            {!onSaveOverride && (

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

            )}



            <section className="settings-section">

              <h3>Presets</h3>

              <div className="presets-list">

                {presets.map((preset, index) => (

                  <div key={index} className="preset-item">

                    <button 

                      className="preset-btn"

                      onClick={() => handleApplyPreset(preset)}

                      title={`Apply ${preset.name}`}

                    >

                      {preset.name}

                    </button>

                    <button 

                      className="preset-delete"

                      onClick={() => handleDeletePreset(index)}

                      title="Delete Preset"

                    >

                      ×

                    </button>

                  </div>

                ))}

              </div>

              <div className="save-preset-control">

                <input 

                  type="text" 

                  placeholder="New preset name..." 

                  value={newPresetName}

                  onChange={(e) => setNewPresetName(e.target.value)}

                  className="preset-input"

                />

                <button 

                  className="button button-secondary"

                  onClick={handleSavePreset}

                  disabled={!newPresetName.trim()}

                >

                  Save Current as Preset

                </button>

              </div>

            </section>



            <section className="settings-section">
              <h3>Council Members</h3>
              <p className="section-description">
                Select which models will participate in Stage 1 and Stage 2.
                Each model will provide its own response and review others.
              </p>

              <div className="search-control">
                <input
                  type="text"
                  placeholder="Search models (e.g., 'gpt', 'claude', 'gemini')..."
                  value={modelSearch}
                  onChange={(e) => setModelSearch(e.target.value)}
                  className="model-search-input"
                />
              </div>

              <div className="model-grid">
                {availableModels
                  .filter((model) => {
                    const search = modelSearch.toLowerCase();
                    return (
                      model.name.toLowerCase().includes(search) ||
                      model.id.toLowerCase().includes(search) ||
                      model.provider.toLowerCase().includes(search)
                    );
                  })
                  .sort((a, b) => {
                    // Show selected models first
                    const aSelected = councilModels.includes(a.id);
                    const bSelected = councilModels.includes(b.id);
                    if (aSelected && !bSelected) return -1;
                    if (!aSelected && bSelected) return 1;
                    return 0;
                  })
                  .map((model) => (
                    <div
                      key={model.id}
                      className={`model-card ${
                        councilModels.includes(model.id) ? 'selected' : ''
                      }`}
                      onClick={(e) => {
                        // Don't toggle if clicking the persona input
                        if (
                          e.target.tagName === 'TEXTAREA' ||
                          e.target.tagName === 'LABEL'
                        )
                          return;
                        handleToggleModel(model.id);
                      }}
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

                        {councilModels.includes(model.id) && onSaveOverride && (
                          <div
                            className="model-persona-input"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <label>Role / Persona:</label>
                            <textarea
                              placeholder="You are a skeptical security engineer..."
                              value={modelPersonas[model.id] || ''}
                              onChange={(e) =>
                                setModelPersonas({
                                  ...modelPersonas,
                                  [model.id]: e.target.value,
                                })
                              }
                              rows={2}
                            />
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
              </div>

              <div className="selected-count">
                {councilModels.length} model{councilModels.length !== 1 ? 's' : ''}{' '}
                selected
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
                {availableModels
                  .filter((model) => {
                    const search = modelSearch.toLowerCase();
                    return (
                      model.name.toLowerCase().includes(search) ||
                      model.id.toLowerCase().includes(search) ||
                      model.provider.toLowerCase().includes(search) ||
                      model.id === chairmanModel // Always show selected
                    );
                  })
                  .sort((a, b) => {
                    if (a.provider < b.provider) return -1;
                    if (a.provider > b.provider) return 1;
                    if (a.name < b.name) return -1;
                    if (a.name > b.name) return 1;
                    return 0;
                  })
                  .map((model) => (
                    <option key={model.id} value={model.id}>
                      {model.name} ({model.provider})
                    </option>
                  ))}
              </select>

            </section>



            <div className="settings-actions">

              {!onSaveOverride && (

                <button

                  className="button button-secondary"

                  onClick={handleReset}

                  disabled={saving}

                >

                  Reset to Default

                </button>

              )}

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

                  {saving ? 'Saving...' : saveButtonText}

                </button>

              </div>

            </div>

          </div>

        )}

      </div>

    </div>

  );

}
