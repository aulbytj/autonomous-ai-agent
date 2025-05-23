import { NextPageContext } from 'next';

// This custom error page will catch any errors that occur during rendering
function CustomError({ statusCode }: { statusCode: number }) {
  return (
    <div className="error-container" style={{ 
      padding: '20px', 
      margin: '40px auto',
      maxWidth: '500px',
      backgroundColor: '#f8d7da',
      color: '#721c24',
      borderRadius: '8px',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }}>
      <h1 style={{ fontSize: '24px', marginBottom: '15px' }}>Something went wrong</h1>
      <p style={{ marginBottom: '15px' }}>
        {statusCode
          ? `An error ${statusCode} occurred on the server`
          : 'An error occurred on the client'}
      </p>
      <button 
        onClick={() => window.location.href = '/'}
        style={{
          padding: '8px 16px',
          backgroundColor: '#dc3545',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer'
        }}
      >
        Go to Home
      </button>
    </div>
  );
}

CustomError.getInitialProps = ({ res, err }: NextPageContext) => {
  const statusCode = res ? res.statusCode : err ? (err as any).statusCode ?? 500 : 404;
  
  // Log the error to monitoring service
  if (err) {
    console.error('Error caught in CustomError.getInitialProps:', err);
  }
  
  return { statusCode };
};

export default CustomError;
