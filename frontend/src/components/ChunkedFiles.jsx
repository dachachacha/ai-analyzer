import React, { useState, useEffect } from 'react';
import axios from 'axios';

const ChunkedFiles = ({ project }) => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

  useEffect(() => {
    const fetchFiles = async () => {
      try {
        const response = await axios.get(`${process.env.REACT_APP_API_BASE_URL}/chunked-files?projectName=${project}`);
        setFiles(response.data.files);
      } catch (error) {
        setMessage(`Error fetching files: ${error.message}`);
      } finally {
        setLoading(false);
      }
    };

    fetchFiles();
  }, [project]);

  const handleDelete = async (filePath) => {
    try {
      const response = await axios.post(`${process.env.REACT_APP_API_BASE_URL}/delete-chunked-file`, {
        project,
        filePath,
      });
      setMessage(response.data.message);
      setFiles(files.filter(file => file.filePath !== filePath));
    } catch (error) {
      setMessage(`Error deleting file: ${error.response.data.detail}`);
    }
  };

  if (loading) {
    return <div className="text-center text-gray-500">Loading...</div>;
  }

  return (
    <div className="p-6 bg-white rounded-lg shadow-md max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold mb-4 text-center">Chunked Files</h2>
      {message && (
        <div className="mb-4 p-3 border-l-4 border-blue-500 bg-blue-100 text-blue-700 rounded">
          {message}
        </div>
      )}
      <ul className="space-y-4">
        {files.map(file => (
          <li key={file.filePath} className="flex justify-between items-center p-4 bg-gray-100 rounded shadow">
            <span className="font-medium">{file.filePath} ({file.chunkCount} chunks)</span>
            <button
              onClick={() => handleDelete(file.filePath)}
              className="bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700 transition-colors duration-200"
            >
              Delete
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ChunkedFiles;
