const chat = document.getElementById('chat');
const input = document.getElementById('input');
let history = []; 

function addMessage(role, text, sources) {
  const div = document.createElement('div');
  div.className = `msg ${role}`;
  
  // Format newlines as <br>
  let htmlText = text ? text.replace(/\n/g, '<br>') : '';
  
  div.innerHTML = `<b>${role === 'user' ? 'You' : 'Bot'}:</b> ${htmlText}`;
  
  if (sources && sources.length) {
    const s = document.createElement('div');
    s.className = 'sources';
    s.textContent = 'Sources: ' + sources.join(', ');
    div.appendChild(s);
  }
  
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

async function send() {
  const q = input.value.trim();
  if (!q) return;
  
  // 1. Show user message
  addMessage('user', q);
  input.value = '';

  // 2. Show loading state
  const loadingDiv = document.createElement('div');
  loadingDiv.className = 'msg bot';
  loadingDiv.innerHTML = `<b>Bot:</b> <i>Thinking...</i>`;
  chat.appendChild(loadingDiv);
  chat.scrollTop = chat.scrollHeight;

  try {
    // 3. Send to backend
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: q, history: history })
    });

    // 4. Remove loading state
    loadingDiv.remove();

    if (!res.ok) {
      throw new Error(`Server returned status ${res.status}`);
    }

    const data = await res.json();
    
    // 5. Show bot answer
    addMessage('bot', data.answer, data.sources);

    // 6. Update history
    history.push({ role: 'user', content: q });
    history.push({ role: 'model', content: data.answer });
    if (history.length > 20) {
      history = history.slice(-20);
    }
    
  } catch (err) {
    loadingDiv.remove();
    addMessage('bot', 'Sorry, an error occurred while connecting to the server.');
    console.error('Frontend Error:', err);
  }
}