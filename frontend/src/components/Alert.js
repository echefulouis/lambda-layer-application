import React from 'react';

const Alert = ({ type, message }) => {
  const getIcon = () => {
    switch (type) {
      case 'success':
        return 'check-circle';
      case 'error':
        return 'exclamation-triangle';
      case 'info':
        return 'info-circle';
      default:
        return 'exclamation-triangle';
    }
  };

  return (
    <div className={`alert alert-${type}`}>
      <i className={`fas fa-${getIcon()}`}></i>
      <span>{message}</span>
    </div>
  );
};

export default Alert; 