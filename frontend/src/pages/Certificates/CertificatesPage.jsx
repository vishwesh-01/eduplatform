/**
 * CertificatesPage.jsx — Lists earned certificates with download buttons.
 */

import { useEffect, useState } from 'react';
import { downloadCertificate, getCertificates } from '../../api/certificates';
import styles from './CertificatesPage.module.css';

export default function CertificatesPage() {
  const [certs,     setCerts]     = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [downloading, setDownloading] = useState(null);

  useEffect(() => {
    getCertificates()
      .then(res => setCerts(res.data.data.certificates || []))
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  const handleDownload = async (cert) => {
    setDownloading(cert.certificate_code);
    try {
      const res = await downloadCertificate(cert.certificate_code);
      /* Create a temporary blob URL and trigger download */
      const url  = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href     = url;
      link.download = `certificate-${cert.certificate_code}.pdf`;
      link.click();
      URL.revokeObjectURL(url);
    } catch {
      alert('Download failed. Please try again.');
    } finally {
      setDownloading(null);
    }
  };

  if (isLoading) return <div className={styles.center}>Loading certificates...</div>;

  return (
    <div className={styles.page}>
      <div className={styles.container}>
        <h1 className={styles.title}>Your Certificates</h1>

        {certs.length === 0 ? (
          <div className={styles.empty}>
            <p>You have not earned any certificates yet.</p>
            <p className={styles.hint}>Complete all modules in a course to receive a certificate.</p>
          </div>
        ) : (
          <div className={styles.grid}>
            {certs.map(cert => (
              <div key={cert.id} className={styles.card}>
                <div className={styles.cardTop}>
                  <h2 className={styles.courseTitle}>{cert.course_title}</h2>
                  <p className={styles.issuedDate}>
                    Issued: {cert.issued_at ? new Date(cert.issued_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' }) : 'Unknown'}
                  </p>
                  <p className={styles.certCode}>ID: {cert.certificate_code}</p>
                </div>
                <button
                  className={styles.btnDownload}
                  onClick={() => handleDownload(cert)}
                  disabled={downloading === cert.certificate_code}
                >
                  {downloading === cert.certificate_code ? 'Downloading...' : 'Download PDF'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
