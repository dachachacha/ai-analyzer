import React, { useEffect, useState } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'

function QueryHistory() {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchHistory = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await axios.get(`${process.env.REACT_APP_API_BASE_URL}/history`)
      setHistory(response.data)
    } catch (err) {
      setError('Failed to load query history.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHistory()
  }, [])

  return (
    <div className="max-w-3xl mx-auto">
      <h2 className="text-xl font-bold mb-4">Query History</h2>

      <div className="mb-4 flex justify-between items-center">
        <button
          onClick={fetchHistory}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors duration-200"
        >
          Refresh History
        </button>
        {loading && <p className="text-gray-500">Refreshing...</p>}
      </div>

      {loading && !history.length ? (
        <p>Loading query history...</p>
      ) : error ? (
        <p className="text-red-500">{error}</p>
      ) : history.length === 0 ? (
        <p className="text-gray-500">No queries found.</p>
      ) : (
        <div className="space-y-4">
          {history.map((entry, index) => (
            <div
              key={index}
              className="border rounded p-4 bg-gray-100 shadow-sm hover:shadow-md transition-shadow"
            >
              <p><span className="font-semibold">Query:</span> {entry.query}</p>
              <div>
                <span className="font-semibold">Answer:</span>
                <ReactMarkdown className="mt-2 prose prose-sm">{entry.answer}</ReactMarkdown>
              </div>
              <p className="text-sm text-gray-500">
                <span className="font-semibold">Timestamp:</span> {new Date(entry.timestamp).toLocaleString()}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default QueryHistory

