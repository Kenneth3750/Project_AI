import React, { useState, useEffect } from 'react';
import { Camera, Mic, MapPin, Settings, AlertTriangle } from 'lucide-react';

const PermissionHandler = ({ onAllPermissionsGranted }) => {
  const [permissions, setPermissions] = useState({
    camera: 'prompt',
    microphone: 'prompt',
    location: 'prompt'
  });
  const [showDialog, setShowDialog] = useState(false);
  const [showInstructions, setShowInstructions] = useState(false);

  useEffect(() => {
    checkPermissions();
  }, []);

  const checkPermissions = async () => {
    const camera = await navigator.permissions.query({ name: 'camera' });
    const microphone = await navigator.permissions.query({ name: 'microphone' });
    const geolocation = await navigator.permissions.query({ name: 'geolocation' });

    setPermissions({
      camera: camera.state,
      microphone: microphone.state,
      location: geolocation.state
    });

    if (camera.state === 'granted' && microphone.state === 'granted' && geolocation.state === 'granted') {
      onAllPermissionsGranted();
    } else {
      setShowDialog(true);
      if (camera.state === 'denied' || microphone.state === 'denied' || geolocation.state === 'denied') {
        setShowInstructions(true);
      }
    }
  };

  const requestPermissions = async () => {
    try {
      if (permissions.camera !== 'granted') {
        await navigator.mediaDevices.getUserMedia({ video: true });
      }
      if (permissions.microphone !== 'granted') {
        await navigator.mediaDevices.getUserMedia({ audio: true });
      }
      if (permissions.location !== 'granted') {
        await new Promise((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject);
        });
      }
      checkPermissions();
    } catch (error) {
      console.error('Error requesting permissions:', error);
      setShowInstructions(true);
    }
  };

  const getBrowserInstructions = () => {
    let instructions;
    if (navigator.userAgent.includes('Chrome')) {
      instructions = (
        <ol className="list-decimal list-inside">
          <li>Click the lock icon (🔒) in the address bar or not secure if you are on a testing enviroment</li>
          <li>Click on "Site settings"</li>
          <li>Find each blocked permission (Camera, Microphone, Location)</li>
          <li>Change the setting from "Block" to "Allow"</li>
          <li>Refresh the page after changing settings</li>
        </ol>
      );
    } else if (navigator.userAgent.includes('Firefox')) {
      instructions = (
        <ol className="list-decimal list-inside">
          <li>Click the lock icon (🔒) in the address bar</li>
          <li>Click on "Connection secure" or "Connection not secure"</li>
          <li>Click on "More Information"</li>
          <li>Go to the "Permissions" tab</li>
          <li>Find each blocked permission and change it to "Allow"</li>
          <li>Refresh the page after changing settings</li>
        </ol>
      );
    } else {
      instructions = (
        <p>Please check your browser settings and allow Camera, Microphone, and Location permissions for this site. After changing the settings, please refresh the page.</p>
      );
    }

    return (
      <div className="mt-4 p-4 bg-yellow-100 rounded-md">
        <h3 className="font-bold mb-2 flex items-center">
          <AlertTriangle className="mr-2 text-yellow-600" />
          Important: Permissions are blocked
        </h3>
        <p className="mb-2">To use this application, you must change your browser settings:</p>
        {instructions}
      </div>
    );
  };

  if (!showDialog) {
    return null;
  }

  const isAnyPermissionDenied = Object.values(permissions).some(p => p === 'denied');

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-lg max-w-md w-full">
        <h2 className="text-xl font-bold mb-4">Permissions Required</h2>
        <p className="mb-4">
          This app requires camera, microphone, and location permissions to function properly. 
          {isAnyPermissionDenied ? " Some permissions are currently blocked." : " Please grant these permissions to continue."}
        </p>
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="text-center">
            <Camera className={`mx-auto h-8 w-8 ${permissions.camera === 'granted' ? 'text-green-500' : 'text-red-500'}`} />
            <p className="mt-2 font-semibold">Camera</p>
          </div>
          <div className="text-center">
            <Mic className={`mx-auto h-8 w-8 ${permissions.microphone === 'granted' ? 'text-green-500' : 'text-red-500'}`} />
            <p className="mt-2 font-semibold">Microphone</p>
          </div>
          <div className="text-center">
            <MapPin className={`mx-auto h-8 w-8 ${permissions.location === 'granted' ? 'text-green-500' : 'text-red-500'}`} />
            <p className="mt-2 font-semibold">Location</p>
          </div>
        </div>
        {isAnyPermissionDenied && getBrowserInstructions()}
        <div className="flex justify-end space-x-2 mt-4">
          <button onClick={() => {setShowDialog(false)
            window.location.href = "/";
          }} className="px-4 py-2 bg-gray-200 rounded">
            Cancel
          </button>
          {!isAnyPermissionDenied && (
            <button onClick={requestPermissions} className="px-4 py-2 bg-blue-500 text-white rounded">
              Request Permissions
            </button>
          )}
          {isAnyPermissionDenied && (
            <button onClick={() => window.location.reload()} className="px-4 py-2 bg-green-500 text-white rounded flex items-center">
              <Settings className="mr-2" size={16} />
              Refresh Page
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default PermissionHandler;