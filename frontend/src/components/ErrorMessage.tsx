export function ErrorMessage({ message }: { message: string }) {
  return <div className="message error" role="alert"><strong>Request unsuccessful</strong><span>{message}</span></div>;
}

