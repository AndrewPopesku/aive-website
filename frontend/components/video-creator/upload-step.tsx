        <div className="flex flex-col items-center justify-center w-full h-64 border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
          <div className="flex flex-col items-center justify-center">
            <CloudUploadIcon className="h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              {isDragging ? "Drop your audio file here" : "Upload an audio file"}
            </h3>
            <p className="mt-1 text-xs text-gray-500">MP3 or WAV up to 10MB</p>
            <div className="mt-4">
              <label htmlFor="file-upload" className="cursor-pointer bg-white rounded-md font-medium text-primary hover:text-primary-dark focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-primary">
                <span>Select a file</span>
                <input
                  id="file-upload"
                  name="file-upload"
                  type="file"
                  className="sr-only"
                  accept="audio/mpeg,audio/mp3,audio/wav,audio/x-wav"
                  onChange={handleFileChange}
                />
              </label>
            </div>
          </div>
        </div> 