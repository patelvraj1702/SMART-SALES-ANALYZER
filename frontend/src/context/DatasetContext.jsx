import { createContext, useContext, useState } from 'react'

const DatasetContext = createContext(null)

export function DatasetProvider({ children }) {
  const [selectedUploadId, setSelectedUploadId] = useState(null)
  const [selectedUpload, setSelectedUpload] = useState(null)

  const selectUpload = (upload) => {
    setSelectedUpload(upload)
    setSelectedUploadId(upload?.id || null)
  }

  return (
    <DatasetContext.Provider value={{ selectedUploadId, selectedUpload, selectUpload }}>
      {children}
    </DatasetContext.Provider>
  )
}

export function useDataset() {
  return useContext(DatasetContext)
}
