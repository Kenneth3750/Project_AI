import React, { useContext, useState, useEffect } from "react";
import { useChat } from "../hooks/useChat";
import { useNotification } from './NotificationContext';
import SubtitlesContext from './subtitles'; 
import HelpTooltip from "./HelpToolTip";



export const UI = ({ hidden, ...props }) => {
  const { loading, cameraZoomed, setCameraZoomed, displayResponses } = useChat();
  const { subtitles } = useContext(SubtitlesContext);
  const [accumulatedResponses, setAccumulatedResponses] = useState([]);
  const [infoContent, setInfoContent] = useState("Initial content from server...");
  const [isOpen, setIsOpen] = useState(false);
  const [pdfError, setPdfError] = useState("");
  const [uploadedPdf, setUploadedPdf] = useState(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [hasNewContent, setHasNewContent] = useState(false);
  const [storedPdfName, setStoredPdfName] = useState("");
  const [isAudioPlaying, setIsAudioPlaying] = useState(false);
  const [avatarStatus, setAvatarStatus] = useState("Sleeping");
  const [naiaRole, setNaiaRole] = useState("Default Role");
  const [universityEmail, setUniversityEmail] = useState("");
  const [activeEmail, setActiveEmail] = useState("");
  const [emailError, setEmailError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const { notifications } = useNotification();


  useEffect(() => {
    const storedName = window.localStorage.getItem("pdfFilename");
    if (storedName) {
      setStoredPdfName(storedName);
    }
  }, []);

  const handleLanguageChange = (e) => {
    const newLanguage = e.target.value;
    setLanguage(newLanguage);
    window.dispatchEvent(new CustomEvent('languageChanged', { detail: { language: newLanguage } }));
  };

  useEffect(() => {
    const handleRoleUpdate = (event) => {
      setNaiaRole(event.detail.role);
    };

    window.addEventListener('naiaRoleUpdated', handleRoleUpdate);
    window.dispatchEvent(new Event('reactComponentReady'));
    return () => {
      window.removeEventListener('naiaRoleUpdated', handleRoleUpdate);
    };
  }, []);

  useEffect(() => {
    const handleAvatarStatusChange = (event) => {
      console.log("Avatar status changed to:", event.detail.status);
      setAvatarStatus(event.detail.status);
    };

    window.addEventListener('avatarStatusChanged', handleAvatarStatusChange);

    return () => {
      window.removeEventListener('avatarStatusChanged', handleAvatarStatusChange);
    };
  }, []);

  useEffect(() => {
    const handleRecordingChange = (event) => {
      setIsRecording(event.detail.isRecording);
    };

    window.addEventListener('recordingStatusChanged', handleRecordingChange);

    return () => {
      window.removeEventListener('recordingStatusChanged', handleRecordingChange);
    };
  }, []);

  useEffect(() => {
    const handleAudioStatusChange = (event) => {
      setIsAudioPlaying(event.detail.isPlaying);
    };

    window.addEventListener('audioStatusChanged', handleAudioStatusChange);

    return () => {
      window.removeEventListener('audioStatusChanged', handleAudioStatusChange);
    };
  }, []);

  useEffect(() => {
    const handleModalVisibility = (event) => {
      setIsModalVisible(event.detail.visible);
    };

    window.addEventListener('modalVisibilityChanged', handleModalVisibility);

    return () => {
      window.removeEventListener('modalVisibilityChanged', handleModalVisibility);
    };
  }, []);

  useEffect(() => {
    if (displayResponses && displayResponses.length > 0) {
      const newResponses = displayResponses.map(response => ({
        content: response.display || response.fragment,
        timestamp: new Date().toLocaleTimeString()
      }));
      
      setAccumulatedResponses(prevResponses => [...newResponses, ...prevResponses]);
      
      if (window.innerWidth < 640) { // 640px is the 'sm' breakpoint in Tailwind
        setHasNewContent(true);
      } else {
        setIsOpen(true);
      }
    }
  }, [displayResponses]);

  useEffect(() => {
    fetchActiveEmail();
  }, []);

  const fetchActiveEmail = async () => {
    try {
      const response = await fetch('/university', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      if (response.ok) {
        const data = await response.json();
        setActiveEmail(data.email || "");
      } else {
        console.error('Failed to fetch active email');
      }
    } catch (error) {
      console.error('Error fetching active email:', error);
    }
  };

  const handleEmailSubmit = async (e) => {
    e.preventDefault();
    setEmailError("");
    setSuccessMessage("");

    if (!universityEmail.endsWith("@uninorte.edu.co")) {
      setEmailError("Please enter a valid Uninorte email address.");
      return;
    }

    try {
      const response = await fetch('/university', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: universityEmail }),
      });

      if (response.ok) {
        setActiveEmail(universityEmail);
        setUniversityEmail("");
        setSuccessMessage("Email updated successfully!");
        setTimeout(() => setSuccessMessage(""), 3000); // Clear message after 3 seconds
      } else {
        const errorData = await response.json();
        setEmailError(errorData.error || "Failed to save email.");
      }
    } catch (error) {
      console.error('Error saving email:', error);
      setEmailError("An error occurred while saving the email.");
    }
  };



  useEffect(() => {
    console.log("Current avatar status:", avatarStatus);
    console.log("Status text:", getStatusText(avatarStatus));
  }, [avatarStatus]);

  const getStatusColor = (status) => {
    switch(status) {
      case "Listening": return "bg-green-500";
      case "Speaking": return "bg-blue-500";
      case "Thinking": return "bg-yellow-500";
      case "Sleeping": return "bg-gray-500";
      default: return "bg-gray-500";
    }
  };

  const getStatusText = (status) => {
    switch(status) {
      case "Listening": return "Listening...";
      case "Speaking": return "Speaking...";
      case "Thinking": return "Thinking...";
      case "Sleeping": return "Sleeping...";
      default: return "Sleeping...";
    }
  };

  const copyToClipboard = () => {
    const textContent = accumulatedResponses
      .map(response => `[${response.timestamp}] ${response.content}`)
      .join('\n\n');
    navigator.clipboard.writeText(textContent);
  };

  const handlePdfUpload = async (event) => {
    const file = event.target.files[0];
    if (file.size > 30 * 1024 * 1024) {
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
        setStoredPdfName(file.name);
        window.localStorage.setItem("pdfFilename", file.name);
        setPdfError("");
      }
    } catch (error) {
      setPdfError("An error occurred while uploading the PDF.");
    }
  };

  const toggleContent = () => {
    setIsOpen(!isOpen);
    setHasNewContent(false);
  };

  if (hidden) {
    return null;
  }

  
  return (
    <>
        
        <div className="fixed inset-0 z-10 flex flex-col justify-between p-4 pointer-events-none">
          <div className="fixed top-4 right-4 z-50">
            {notifications.map(notification => (
              <div
                key={notification.id}
                className={`mb-2 p-2 rounded shadow-lg ${
                  notification.type === 'error' ? 'bg-red-500' : 'bg-blue-500'
                } text-white`}
              >
                {notification.message}
              </div>
            ))}
          </div>
          {/* Contenido principal */}
          <div className="flex justify-between items-start w-full">
          {/* Panel izquierdo (existente) */}
          <div className="self-start backdrop-blur-md bg-white bg-opacity-20 p-3 rounded-lg pointer-events-auto max-w-[200px] relative">
            <div className="flex justify-between items-center">
              <h1 className="font-bold text-lg text-gray-800">NAIA</h1>
              <HelpTooltip role={naiaRole} />
            </div>
            <h6 id="user_name" className="text-xs text-gray-700">Current user: Unknown</h6>
            <h6 id="naia-role" className="text-xs text-gray-700">
                Role: {naiaRole}
            </h6>
            <button
              onClick={toggleContent}
              className="mt-2 text-blue-500 hover:text-blue-600 rounded-md p-1 text-sm pointer-events-auto"
            >
              {isOpen ? "Hide Content" : "Show Content"}
            </button>
            {hasNewContent && (
              <div className="absolute top-0 right-0 w-3 h-3 bg-red-500 rounded-full"></div>
            )}

          {isOpen && (
            <>
              <div className="mt-2 p-2 bg-gray-100 rounded-md w-full h-40 overflow-y-auto pointer-events-auto">
                <h2 className="font-semibold text-sm mb-1">Requested functions</h2><br>
                </br>
                {accumulatedResponses.map((response, index) => (
                  <div key={index} className="text-xs mb-2">
                    <span className="font-semibold">[{response.timestamp}]</span>
                    <div dangerouslySetInnerHTML={{ __html: response.content }}></div>
                  </div>
                ))}
                <button
                  onClick={copyToClipboard}
                  className="mt-2 bg-blue-500 hover:bg-blue-600 text-white p-1 rounded-md text-xs pointer-events-auto"
                >
                  Copy to clipboard
                </button>
              </div>

              { naiaRole === "Investigator" && (
              <div className="mt-2">
                <h2 className="font-semibold text-sm mb-1">Upload PDF</h2>
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={handlePdfUpload}
                  className="mb-1 text-xs w-full"
                />
                {pdfError && <p className="text-red-500 text-xs">{pdfError}</p>}
                {(uploadedPdf || storedPdfName) && (
                  <div className="flex items-center text-xs">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      className="w-4 h-4 text-red-500 mr-1"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.74 9L14 4.54 8 9h3v9h2V9h3z" />
                    </svg>
                    <span className="truncate">{uploadedPdf ? uploadedPdf.name : storedPdfName}</span>
                  </div>
                )}
              </div>
            )}

              {( naiaRole === "University Guide") && (
              <div className="mt-4">
                  <h2 className="font-semibold text-sm mb-1">University Email</h2>
                  <p className="text-xs mb-2">Active Email: {activeEmail || "None set"}</p>
                  <form onSubmit={handleEmailSubmit} className="space-y-2">
                    <input
                      type="email"
                      value={universityEmail}
                      onChange={(e) => setUniversityEmail(e.target.value)}
                      placeholder="Enter Uninorte email"
                      className="w-full text-xs p-1 border rounded"
                    />
                    <button
                      type="submit"
                      className="w-full bg-blue-500 hover:bg-blue-600 text-white p-1 rounded-md text-xs"
                    >
                      Set Email
                    </button>
                  </form>
                  {emailError && <p className="text-red-500 text-xs mt-1">{emailError}</p>}
                  {successMessage && (
                    <div className="mt-2 p-2 bg-green-100 border border-green-400 text-green-700 text-xs rounded">
                      {successMessage}
                    </div>
                  )}
                </div>
                )}
            </>
          )}
          </div>
          {/* Nuevo panel derecho para el estado del avatar */}
          <div className="flex flex-col items-end">
            <div className={`backdrop-blur-md bg-white bg-opacity-20 p-3 rounded-lg pointer-events-auto transition-all duration-300 ${getStatusColor(avatarStatus)} mb-2`}>
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full animate-pulse ${getStatusColor(avatarStatus)}`}></div>
                <h6 id="status" className="text-sm font-semibold text-black whitespace-nowrap overflow-visible">                
                  Status: {getStatusText(avatarStatus)}
                </h6>
              </div>
            </div>
            {/* <div className="backdrop-blur-md bg-white bg-opacity-20 p-3 rounded-lg pointer-events-auto">
              <select 
                value={language} 
                onChange={handleLanguageChange}
                className="bg-transparent text-sm font-semibold"
              >
                <option value="en-US">English</option>
                <option value="es-ES">Español</option>
              </select>
            </div> */}
          </div>
        </div>

  
        <div className="flex items-center justify-center flex-grow">
          <p className="text-center text-white bg-black bg-opacity-50 p-2 rounded-md text-xl font-semibold">{subtitles}</p>
        </div>

        {/* Barra de control inferior */}
        <div className="self-end w-full flex justify-between items-end pointer-events-auto">
          <div className="flex space-x-2">
            <a href="/home" className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-2 rounded-full text-xs sm:text-sm">Go to home</a>
            <form action="/logout" method="post" className="inline">
              <button className="bg-red-500 hover:bg-red-600 text-white px-3 py-2 rounded-full text-xs sm:text-sm">LogOut</button>
            </form>
            <button 
                id="recordButton" 
                className={`text-white px-3 py-2 rounded-full text-xs sm:text-sm ${
                  isRecording ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600'
                } ${isAudioPlaying ? 'opacity-50 cursor-not-allowed' : ''}`} 
                onClick={() => !isAudioPlaying && window.toggleRecording()}
                disabled={isAudioPlaying}
                data-recording={isRecording.toString()}
              >
                {isRecording ? 'Stop' : 'Start'}
            </button>
          </div>
          <button
            onClick={() => setCameraZoomed(!cameraZoomed)}
            className="bg-blue-500 hover:bg-blue-600 text-white p-3 rounded-full shadow-lg ml-2"
          >
            {cameraZoomed ? "Zoom Out" : "Zoom In"}
          </button>
        </div>
      </div>

      {/* Modal */}
      <div id="modal" className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-30" style={{ display: isModalVisible ? 'flex' : 'none' }}>
        <div id="modal-content" className="bg-white p-4 rounded-lg shadow-xl text-sm">
          Remember to look at the camera for a better face recognition
        </div>
      </div>
    </>
  );
};