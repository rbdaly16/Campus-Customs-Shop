import { type FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

const MIN_PASSWORD = 8

export default function CreateAccount() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const mismatch = confirm.length > 0 && confirm !== password

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (password !== confirm) {
      setError("Passwords don't match.")
      return
    }
    const form = new FormData(e.currentTarget)
    setError(null)
    setSubmitting(true)
    try {
      await register({
        first_name: String(form.get('first_name')),
        last_name: String(form.get('last_name')),
        email: String(form.get('email')),
        password,
      })
      navigate('/')
    } catch (err) {
      setError((err as Error).message)
      setSubmitting(false)
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <h1>Create account</h1>
      <p className="muted">Join the team. No tryouts required.</p>
      <div className="form-row">
        <label>
          First name
          <input name="first_name" autoComplete="given-name" maxLength={50} required />
        </label>
        <label>
          Last name
          <input name="last_name" autoComplete="family-name" maxLength={50} required />
        </label>
      </div>
      <label>
        Email
        <input type="email" name="email" autoComplete="email" required />
      </label>
      <label>
        Password
        <input
          type="password"
          name="password"
          autoComplete="new-password"
          minLength={MIN_PASSWORD}
          maxLength={128}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <span className="hint">At least {MIN_PASSWORD} characters.</span>
      </label>
      <label>
        Confirm password
        <input
          type="password"
          name="confirm_password"
          autoComplete="new-password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          aria-invalid={mismatch}
          required
        />
        {mismatch && <span className="hint error">Passwords don't match.</span>}
      </label>
      {error && <p className="form-error" role="alert">{error}</p>}
      <button type="submit" className="button" disabled={submitting || mismatch}>
        {submitting ? 'Creating account…' : 'Create account'}
      </button>
      <p className="muted">
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </form>
  )
}
