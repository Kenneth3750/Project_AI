import React, { useContext, useState, useEffect } from "react";
import { useChat } from "../hooks/useChat";
import SubtitlesContext from './subtitles'; 

export const UI = ({ hidden, ...props }) => {
  const { loading, cameraZoomed, setCameraZoomed, displayResponses } = useChat();
  const { subtitles } = useContext(SubtitlesContext);
  const [infoContent, setInfoContent] = useState("Initial content from server...");
  const [isOpen, setIsOpen] = useState(false);
  const [pdfError, setPdfError] = useState("");
  const [uploadedPdf, setUploadedPdf] = useState(null);

  useEffect(() => {
    if (displayResponses && displayResponses.length > 0) {
      const htmlContent = displayResponses.map(response => response.display || response.fragment).join('<br>');
      setInfoContent(htmlContent);
      setIsOpen(true); // Abre el cuadro automáticamente
    }
  }, [displayResponses]);

  const copyToClipboard = () => {
    const tempElement = document.createElement("div");
    tempElement.innerHTML = infoContent;
    // Replace <br> with newline characters
    const textContent = tempElement.textContent.replace(/<br\s*\/?>/gi, '\n') || tempElement.innerText.replace(/<br\s*\/?>/gi, '\n') || "";
    navigator.clipboard.writeText(textContent);
  };

  const handlePdfUpload = async (event) => {
    const file = event.target.files[0];
    if (file.size > 30 * 1024 * 1024) { // 30 MB limit
      setPdfError("The file exceeds the 30MB limit.");
      return;
    }

    const formData = new FormData();
    formData.append("pdf", file);

    try {
      const response = await fetch("/pdfreader", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        setPdfError(errorData.error || "An error occurred while uploading the PDF.");
      } else {
        setUploadedPdf(file);
        setPdfError(""); // Clear any previous errors
      }
    } catch (error) {
      setPdfError("An error occurred while uploading the PDF.");
    }
  };

  const toggleContent = () => {
    setIsOpen(!isOpen);
  };

  if (hidden) {
    return null;
  }

  return (
    <>
      <div className="fixed top-0 left-0 right-0 bottom-0 z-10 flex justify-between p-4 flex-col pointer-events-none">
        <div className="self-start backdrop-blur-md bg-white bg-opacity-50 p-4 rounded-lg pointer-events-auto">
          <h1 className="font-black text-xl">NAIA</h1>
          <button
            onClick={toggleContent}
            className="mt-2 text-blue-500 hover:text-blue-600 rounded-md p-2 pointer-events-auto"
          >
            {isOpen ? (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                className="w-6 h-6"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
              </svg>
            ) : (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                className="w-6 h-6"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
              </svg>
            )}
          </button>

          {isOpen && (
            <>
              <div className="mt-2 p-4 bg-gray-100 rounded-md w-64 h-48 overflow-y-auto pointer-events-auto">
                <h2 className="font-semibold text-lg mb-2">Requested function</h2>
                <div dangerouslySetInnerHTML={{ __html: infoContent }}></div>
                <button
                  onClick={copyToClipboard}
                  className="mt-2 bg-blue-500 hover:bg-blue-600 text-white p-2 rounded-md pointer-events-auto"
                >
                  Copy to clipboard
                </button>
              </div>

              <div className="mt-4">
                <h2 className="font-semibold text-lg mb-2">Upload PDF</h2>
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={handlePdfUpload}
                  className="mb-2"
                />
                {pdfError && <p className="text-red-500">{pdfError}</p>}
                {uploadedPdf && (
                  <div className="flex items-center">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      className="w-6 h-6 text-red-500 mr-2"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.74 9L14 4.54 8 9h3v9h2V9h3z" />
                    </svg>
                    <span>{uploadedPdf.name}</span>
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        <div className="flex items-center justify-center h-full">
          <p className="text-center text-white bg-black bg-opacity-50 p-2 rounded-md text-2xl font-semibold">{subtitles}</p>
        </div>

        <div className="w-full flex flex-col items-end justify-center gap-4">
          <button
            onClick={() => setCameraZoomed(!cameraZoomed)}
            className="pointer-events-auto bg-blue-500 hover:bg-blue-600 text-white p-4 rounded-md"
          >
            {cameraZoomed ? (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
                className="w-6 h-6"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607zM13.5 10.5h-6"
                />
              </svg>
            ) : (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
                className="w-6 h-6"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607zM10.5 7.5v6m3-3h-6"
                />
              </svg>
            )}
          </button>
        </div>
      </div>
    </>
  );
};
