import React, { useState, useEffect } from 'react';

const HelpTooltip = ({ role }) => {
  const [isTooltipVisible, setIsTooltipVisible] = useState(false);
  const [tooltipContent, setTooltipContent] = useState('');

  useEffect(() => {
    const roleContent = {
      'Researcher': (
        <ul className="list-disc pl-4 space-y-1">
          <li>Read and extract information from PDFs (up to 1GB)</li>
          <li>Search for relevant scientific articles using Google Scholar</li>
          <li>Provide easily copyable text fragments for your research</li>
          <li>Generate extended texts on a pdf file</li>
        </ul>
      ),
      'Recepcionist': (
        <ul className="list-disc pl-4 space-y-1">
          <li>Notify residents via WhatsApp about visitors with images</li>
          <li>Send announcements to all residents via WhatsApp</li>
          <li>Manage reservations for common areas</li>
          <li>Recommend places to visit, restaurants, and incoming events on any location</li>
        </ul>
      ),
      'Personal Skills Trainer': (
        <ul className="list-disc pl-4 space-y-1">
          <li>Conduct simulations for real-life scenarios (e.g., job interviews, sales negotiations)</li>
          <li>Practice for language exams with listening and speaking components</li>
          <li>Provide recommendations on social interactions, posture, and attire</li>
        </ul>
      ),
      'Personal Assistant': (
        <ul className="list-disc pl-4 space-y-1">
          <li>Send short emails to pre-registered contacts</li>
          <li>Schedule reminders using Google Calendar or other tools</li>
          <li>Inform about office visitors in your absence</li>
          <li>Keep you on track with your agenda</li>
          <li>Give you information about the weather and recent news</li>
        </ul>
      ),
      'University Guide': (
        <ul className="list-disc pl-4 space-y-1">
          <li>Provide information on academic calendars, important dates, and administrative services</li>
          <li>Offer guidance on key academic processes (e.g., enrollment, flexible progress)</li>
          <li>Connect with student support services and academic counselors</li>
          <li>Send emails with information about resources, libraries, and study spaces to your academic email</li>
        </ul>
      ),
    };

    setTooltipContent(roleContent[role] || 'No information available for this role');
  }, [role]);

  return (
    <div className="relative">
      <button 
        className="bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold"
        onMouseEnter={() => setIsTooltipVisible(true)}
        onMouseLeave={() => setIsTooltipVisible(false)}
      >
        ?
      </button>
      {isTooltipVisible && (
        <div className="absolute z-10 w-64 p-2 mt-2 text-sm bg-white rounded-lg shadow-lg">
          <h6 className="font-semibold mb-2">{role} Functions:</h6>
          {tooltipContent}
        </div>
      )}
    </div>
  );
};

export default HelpTooltip;