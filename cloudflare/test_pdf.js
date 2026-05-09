import fs from 'fs';

async function testPdf() {
  const base64 = fs.readFileSync('/home/krzysiek/Pobrane/2026_05_09_SY7658.pdf', 'base64');
  console.log("Base64 length:", base64.length);
  
  const payload = {
    contents: [
      {
        role: "user",
        parts: [
          { text: "Przeanalizuj PDF dla części: SY7658.\nNajpierw rygorystycznie oceń, czy ten dokument PDF faktycznie dotyczy szukanej części (lub jej wariantu z tej samej rodziny).\nJeśli dokument dotyczy zupełnie innej części, ustaw is_correct_part na false i zignoruj wyciąganie parametrów.\nZwróć JSON o strukturze:\n{\"is_correct_part\": true, \"part_name\":\"\", \"part_number\":\"\", \"description\":\"\", \"category\":\"\", \"species\":\"\", \"genus\":\"\", \"mounting\":\"\", \"value\":\"\", \"keywords\":[\"\"], \"parameters\":{\"Voltage\":\"5V\"}, \"kicad_symbol\":\"\", \"kicad_footprint\":\"\", \"kicad_reference\":\"\", \"confidence\":0.9 }" },
          { inline_data: { mime_type: "application/pdf", data: base64 } }
        ]
      }
    ],
    generationConfig: {
      temperature: 0.1,
      responseMimeType: "application/json"
    }
  };

  const API_KEY = process.env.GEMINI_API_KEY;
  if (!API_KEY) {
    console.log("No API Key");
    return;
  }

  const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key=${API_KEY}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  const json = await res.json();
  console.log(JSON.stringify(json, null, 2));
}

testPdf();
