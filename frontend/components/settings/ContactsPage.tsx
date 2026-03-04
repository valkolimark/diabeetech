'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useKeyboard } from '@/components/VirtualKeyboard'

interface Contact {
  name: string
  phone: string
}

export default function ContactsPage() {
  const { openKeyboard } = useKeyboard()
  const [contacts, setContacts] = useState<Contact[]>([])
  const [newName, setNewName] = useState('')
  const [newPhone, setNewPhone] = useState('')
  const nameRef = useRef<HTMLInputElement>(null)
  const phoneRef = useRef<HTMLInputElement>(null)

  // Sync from virtual keyboard
  useEffect(() => {
    const nameEl = nameRef.current
    const phoneEl = phoneRef.current
    const nameHandler = () => setNewName(nameEl?.value || '')
    const phoneHandler = () => setNewPhone(phoneEl?.value || '')
    nameEl?.addEventListener('input', nameHandler)
    phoneEl?.addEventListener('input', phoneHandler)
    return () => {
      nameEl?.removeEventListener('input', nameHandler)
      phoneEl?.removeEventListener('input', phoneHandler)
    }
  }, [])

  useEffect(() => {
    fetch('/api/contacts')
      .then((r) => r.json())
      .then((data) => { if (Array.isArray(data)) setContacts(data) })
      .catch(() => {})
  }, [])

  const saveContacts = useCallback(async (updated: Contact[]) => {
    try {
      await fetch('/api/contacts', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updated),
      })
      setContacts(updated)
    } catch {}
  }, [])

  const addContact = () => {
    if (!newName.trim() || !newPhone.trim()) return
    saveContacts([...contacts, { name: newName.trim(), phone: newPhone.trim() }])
    setNewName('')
    setNewPhone('')
    if (nameRef.current) nameRef.current.value = ''
    if (phoneRef.current) phoneRef.current.value = ''
  }

  const removeContact = (index: number) => {
    saveContacts(contacts.filter((_, i) => i !== index))
  }

  return (
    <div className="max-w-lg">
      <h2 className="text-xl font-body font-semibold text-white mb-1">Emergency Contacts</h2>
      <p className="text-sm font-body text-white/40 mb-6">
        Receive SMS alerts when glucose is critical
      </p>

      <div className="space-y-2 mb-6">
        {contacts.length === 0 && (
          <div className="text-sm font-body text-white/30 py-4 text-center">
            No contacts added
          </div>
        )}
        {contacts.map((c, i) => (
          <div
            key={i}
            className="flex items-center justify-between px-4 py-3 rounded-xl"
            style={{ background: 'rgba(255,255,255,0.04)' }}
          >
            <div>
              <div className="text-sm font-body text-white">{c.name}</div>
              <div className="text-xs font-body text-white/40">{c.phone}</div>
            </div>
            <button
              onClick={() => removeContact(i)}
              className="text-red-400 hover:text-red-300 text-xs font-body"
            >
              Remove
            </button>
          </div>
        ))}
      </div>

      <div className="space-y-3 p-4 rounded-xl" style={{ background: 'rgba(255,255,255,0.04)' }}>
        <div className="text-xs font-body text-white/50 uppercase tracking-wider">Add Contact</div>
        <input
          ref={nameRef}
          type="text"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onFocus={() => openKeyboard(nameRef as React.RefObject<HTMLInputElement>)}
          placeholder="Name"
          className="w-full px-3 py-2 rounded-lg text-white font-body text-sm outline-none"
          style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)' }}
        />
        <input
          ref={phoneRef}
          type="tel"
          value={newPhone}
          onChange={(e) => setNewPhone(e.target.value)}
          onFocus={() => openKeyboard(phoneRef as React.RefObject<HTMLInputElement>, true)}
          placeholder="Phone number"
          className="w-full px-3 py-2 rounded-lg text-white font-body text-sm outline-none"
          style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)' }}
        />
        <button
          onClick={addContact}
          disabled={!newName.trim() || !newPhone.trim()}
          className="w-full py-2 rounded-lg text-sm font-body font-semibold transition-colors"
          style={{
            background: (!newName.trim() || !newPhone.trim()) ? 'rgba(255,255,255,0.06)' : '#3b82f6',
            color: (!newName.trim() || !newPhone.trim()) ? 'rgba(255,255,255,0.3)' : '#fff',
          }}
        >
          Add Contact
        </button>
      </div>
    </div>
  )
}
