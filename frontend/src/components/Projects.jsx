import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

function Projects({ setCurrentProject }) {
  const [projects, setProjects] = useState([]);
  const [newProjectName, setNewProjectName] = useState('');
  const [folderName, setFolderName] = useState('');
  const [notification, setNotification] = useState(null);

  const logEvent = (message, data = null) => {
    if (data) {
      console.log(`[Projects] ${message}`, data);
    } else {
      console.log(`[Projects] ${message}`);
    }
  };

  const renderNotification = () => {
    if (!notification) return null;

    const notificationStyles = {
      info: 'bg-blue-100 text-blue-700 border-blue-500',
      success: 'bg-green-100 text-green-700 border-green-500',
      error: 'bg-red-100 text-red-700 border-red-500',
    };

    return (
      <div className={`p-3 border-l-4 rounded mb-4 ${notificationStyles[notification.type]}`}>
        {notification.message}
      </div>
    );
  };

  const fetchProjects = useCallback(async () => {
    logEvent('Fetching projects');
    setNotification({ type: 'info', message: 'Loading projects...' });

    try {
      const response = await axios.get(`${process.env.REACT_APP_API_BASE_URL}/projects`);
      setProjects(response.data.projects || []);
      setNotification({ type: 'success', message: 'Projects loaded successfully.' });
    } catch (err) {
      logEvent('Error fetching projects', { error: err });
      setNotification({ type: 'error', message: 'Failed to load projects.' });
    }
  }, []);

  const handleAddProject = async () => {
    if (!newProjectName.trim() || !folderName.trim()) {
      setNotification({ type: 'error', message: 'Both project name and folder name are required.' });
      return;
    }

    logEvent('Adding new project');
    setNotification({ type: 'info', message: 'Adding new project...' });

    try {
      await axios.post(`${process.env.REACT_APP_API_BASE_URL}/projects`, {
        name: newProjectName,
        folder: folderName,
      });

      setProjects([...projects, { name: newProjectName, folder: folderName }]);
      setNewProjectName('');
      setFolderName('');
      setNotification({ type: 'success', message: 'Project added successfully.' });
    } catch (err) {
      logEvent('Error adding project', { error: err });
      setNotification({ type: 'error', message: 'Failed to add project. Please try again.' });
    }
  };

  const handleDeleteProject = async (projectName) => {
    logEvent(`Deleting project: ${projectName}`);
    setNotification({ type: 'info', message: `Deleting project ${projectName}...` });

    try {
      await axios.delete(`${process.env.REACT_APP_API_BASE_URL}/projects`, {
        data: { name: projectName },
      });

      setProjects(projects.filter((project) => project.name !== projectName));
      setNotification({ type: 'success', message: 'Project deleted successfully.' });
    } catch (err) {
      logEvent('Error deleting project', { error: err });
      setNotification({ type: 'error', message: 'Failed to delete project. Please try again.' });
    }
  };

  const handleFlushAllProjects = async () => {
    logEvent('Flushing all projects');
    setNotification({ type: 'info', message: 'Flushing all projects...' });

    try {
      await axios.delete(`${process.env.REACT_APP_API_BASE_URL}/projects/all`);
      setProjects([]); // Clear all projects from state
      localStorage.clear(); // Clear local storage
      setNotification({ type: 'success', message: 'All projects flushed successfully.' });
    } catch (err) {
      logEvent('Error flushing all projects', { error: err });
      setNotification({ type: 'error', message: 'Failed to flush all projects. Please try again.' });
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  return (
    <div className="p-4 bg-white rounded shadow-md max-w-3xl mx-auto">
      <h2 className="text-xl font-bold mb-4">Projects</h2>

      {renderNotification()}

      <div className="mb-4">
        <label className="block text-gray-700">Create a new project</label>
        <div className="flex mt-2 space-x-2">
          <input
            type="text"
            value={newProjectName}
            onChange={(e) => setNewProjectName(e.target.value)}
            className="border rounded p-2 flex-grow"
            placeholder="Project Name"
          />
          <input
            type="text"
            value={folderName}
            onChange={(e) => setFolderName(e.target.value)}
            className="border rounded p-2 flex-grow"
            placeholder="Folder Name"
          />
          <button
            onClick={handleAddProject}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Add
          </button>
        </div>
      </div>

      <div className="mb-4">
        <button
          onClick={handleFlushAllProjects}
          className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
        >
          Flush All Projects
        </button>
      </div>

      <ul className="space-y-2">
        {projects.map((project) => (
          <li
            key={project.name}
            className="flex justify-between items-center p-2 border rounded hover:shadow"
          >
            <span>
              {project.name} <small className="text-gray-500">({project.folder})</small>
            </span>
            <div className="flex space-x-2">
              <button
                onClick={() => setCurrentProject(project.name)}
                className="bg-green-600 text-white px-2 py-1 rounded hover:bg-green-700"
              >
                Load
              </button>
              <button
                onClick={() => handleDeleteProject(project.name)}
                className="bg-red-600 text-white px-2 py-1 rounded hover:bg-red-700"
              >
                Delete
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default Projects;

