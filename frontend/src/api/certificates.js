/**
 * api/certificates.js — Certificate API calls.
 */

import apiClient from './axiosInstance';

/** List all certificates for the authenticated learner */
export const getCertificates = () => apiClient.get('/certificates');

/**
 * Download a certificate PDF as a Blob.
 * The caller creates a temporary object URL and triggers the download.
 */
export const downloadCertificate = (certificateCode) =>
  apiClient.get(`/certificates/${certificateCode}/download`, { responseType: 'blob' });
