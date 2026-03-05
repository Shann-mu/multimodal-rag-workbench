import React from 'react';

import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { hasAccessToken } from '../modules/authToken';

const RequireAuth: React.FC = () => {
  const location = useLocation();

  if (!hasAccessToken()) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
};

export default RequireAuth;