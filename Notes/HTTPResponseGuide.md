# HTTP Responses – C# Client & Python Server

> **Ziel dieses Dokuments:** Verstehen, wie HTTP-Antworten funktionieren, wie man sie in Python (Flask) korrekt zurückgibt und wie man sie in C# richtig empfängt und verarbeitet.

---

## 1. Grundlagen: Was ist eine HTTP Response?

Jede HTTP-Kommunikation folgt dem **Request → Response**-Prinzip:

1. Der **Client** (z. B. deine C#-App) schickt einen Request an den Server
2. Der **Server** (z. B. dein Python-Backend) verarbeitet ihn und schickt eine Response zurück
3. Der Client liest die Response aus und reagiert entsprechend

Eine HTTP Response besteht immer aus drei Teilen:

| Teil | Beschreibung | Beispiel |
|------|-------------|---------|
| **Status Line** | Statuscode + kurze Beschreibung | `HTTP/1.1 200 OK` |
| **Headers** | Metadaten zur Antwort | `Content-Type: application/json` |
| **Body** | Die eigentlichen Daten (optional) | `{"videos": [...]}` |

---

## 2. HTTP Status Codes – Übersicht

Status Codes sind dreistellige Zahlen, die dem Client sagen, **ob und wie** der Request erfolgreich war. Sie sind in Gruppen eingeteilt:

### 2xx – Erfolg ✅
| Code | Name | Wann benutzen |
|------|------|--------------|
| `200` | OK | Standard-Erfolg bei GET, PUT, DELETE |
| `201` | Created | Neue Ressource wurde angelegt (nach POST) |
| `204` | No Content | Erfolg, aber kein Body (z. B. nach DELETE) |

### 4xx – Client-Fehler ⚠️
*Der Client hat etwas falsch gemacht – z. B. fehlerhafte Daten gesendet.*

| Code | Name | Wann benutzen |
|------|------|--------------|
| `400` | Bad Request | Ungültige oder fehlende Parameter |
| `401` | Unauthorized | Nicht authentifiziert (kein/falscher Token) |
| `403` | Forbidden | Authentifiziert, aber keine Berechtigung |
| `404` | Not Found | Ressource existiert nicht |
| `422` | Unprocessable Entity | Daten valide, aber semantisch falsch |

### 5xx – Server-Fehler 🔥
*Der Server hat einen Fehler gemacht – der Client kann nichts dafür.*

| Code | Name | Wann benutzen |
|------|------|--------------|
| `500` | Internal Server Error | Unerwarteter Fehler im Code |
| `503` | Service Unavailable | Server überlastet oder nicht bereit |

---

## 3. Python (Flask) – Responses richtig zurückgeben

### 3.1 Einfache JSON-Antwort

```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/videos")
def get_videos():
    data = {"videos": ["vid1", "vid2", "vid3"]}
    return jsonify(data), 200
```

`jsonify()` macht zwei Dinge automatisch:
- Konvertiert das Python-Dictionary in einen JSON-String
- Setzt den Header `Content-Type: application/json`

Der zweite Rückgabewert `200` ist der **Status Code**. Ohne Angabe nimmt Flask standardmäßig `200`.

---

### 3.2 Fehler korrekt zurückgeben

```python
@app.route("/video/<int:video_id>")
def get_video(video_id):
    video = database.find(video_id)  # Beispiel-Datenbankaufruf

    # ❌ Nicht gefunden → 404
    if video is None:
        return jsonify({"error": f"Video mit ID {video_id} nicht gefunden"}), 404

    # ✅ Gefunden → 200
    return jsonify(video), 200
```

**Wichtig:** Gib bei Fehlern immer ein JSON-Objekt mit einem `"error"` Key zurück.
So kann der C#-Client den Fehler gezielt auslesen.

---

### 3.3 Expliziter Response mit `make_response`

Wenn du mehr Kontrolle über den Response brauchst (z. B. eigene Headers setzen):

```python
from flask import make_response, jsonify

@app.route("/data")
def get_data():
    data = {"result": "ok"}

    response = make_response(jsonify(data))
    response.status_code = 200
    response.headers["X-Custom-Header"] = "PyScrapper/1.0"  # eigener Header
    response.headers["Cache-Control"] = "no-cache"
    return response
```

---

### 3.4 POST-Endpoint mit Validierung

```python
from flask import request

@app.route("/scrape", methods=["POST"])
def start_scrape():
    body = request.get_json()  # JSON-Body aus dem Request lesen

    # Eingabe validieren
    if not body or "url" not in body:
        return jsonify({"error": "Fehlender Parameter: 'url'"}), 400

    url = body["url"]

    try:
        result = scrape(url)  # deine Scraper-Logik
        return jsonify({"success": True, "data": result}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 422  # Unprocessable Entity
    except Exception as e:
        return jsonify({"error": "Interner Fehler", "detail": str(e)}), 500
```

---

### 3.5 Globale Fehlerbehandlung mit `@app.errorhandler`

Statt in jedem Endpoint Fehler einzeln zu behandeln, kannst du globale Handler registrieren:

```python
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route nicht gefunden"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Interner Serverfehler"}), 500
```

Das ist besonders nützlich, damit dein C#-Client immer ein konsistentes JSON-Format bekommt – auch bei unerwarteten Fehlern.

---

## 4. C# – `HttpResponseMessage` richtig lesen

### 4.1 Grundstruktur eines Requests

```csharp
using System.Net.Http;
using System.Net.Http.Json;

public class ApiService
{
    // HttpClient sollte NICHT in jeder Methode neu erstellt werden!
    // Einmal als Feld oder per Dependency Injection verwenden.
    private readonly HttpClient _httpClient;

    public ApiService(HttpClient httpClient)
    {
        _httpClient = httpClient;
    }
}
```

**⚠️ Häufiger Fehler:** `new HttpClient()` in einer Schleife oder Methode aufrufen.
Das verbraucht Sockets und kann zu Fehlern führen. Immer eine **geteilte Instanz** benutzen.

---

### 4.2 Die wichtigsten Properties von `HttpResponseMessage`

```csharp
HttpResponseMessage response = await _httpClient.GetAsync("http://localhost:5000/videos");

// Status Code als Enum
HttpStatusCode statusEnum = response.StatusCode;         // z.B. HttpStatusCode.OK
int statusInt = (int)response.StatusCode;               // z.B. 200
string statusText = response.ReasonPhrase;              // z.B. "OK", "Not Found"

// Schnelle Prüfung: war der Request erfolgreich? (true bei 200–299)
bool success = response.IsSuccessStatusCode;

// Den Body lesen (als String)
string body = await response.Content.ReadAsStringAsync();

// Den Body direkt in ein C#-Objekt deserialisieren
MyClass? obj = await response.Content.ReadFromJsonAsync<MyClass>();

// Response-Header lesen
string? contentType = response.Content.Headers.ContentType?.MediaType;
```

---

### 4.3 Normaler GET-Request mit Fehlerbehandlung

```csharp
public async Task<List<Video>?> GetVideosAsync()
{
    HttpResponseMessage response = await _httpClient.GetAsync("http://localhost:5000/videos");

    // Prüfen ob der Request erfolgreich war (Status 200–299)
    if (!response.IsSuccessStatusCode)
    {
        string errorJson = await response.Content.ReadAsStringAsync();
        Console.WriteLine($"Fehler {(int)response.StatusCode}: {errorJson}");
        return null;
    }

    // Body direkt in ein Objekt deserialisieren
    VideoResponse? result = await response.Content.ReadFromJsonAsync<VideoResponse>();
    return result?.Videos;
}

// Passendes DTO (Data Transfer Object)
public record VideoResponse(List<Video> Videos);
public record Video(string Id, string Title, string ThumbnailUrl);
```

---

### 4.4 POST-Request mit JSON-Body

```csharp
public async Task<bool> StartScrapeAsync(string url)
{
    // PostAsJsonAsync serialisiert das Objekt automatisch als JSON
    var payload = new { Url = url };
    HttpResponseMessage response = await _httpClient.PostAsJsonAsync(
        "http://localhost:5000/scrape", payload
    );

    if (response.StatusCode == HttpStatusCode.Created)  // 201
    {
        Console.WriteLine("Scraping gestartet!");
        return true;
    }

    if (response.StatusCode == HttpStatusCode.BadRequest)  // 400
    {
        var error = await response.Content.ReadFromJsonAsync<ErrorResponse>();
        Console.WriteLine($"Validierungsfehler: {error?.Error}");
        return false;
    }

    return false;
}

public record ErrorResponse(string Error, string? Detail);
```

---

### 4.5 `EnsureSuccessStatusCode()` – Wann benutzen?

```csharp
// EnsureSuccessStatusCode() wirft eine HttpRequestException wenn StatusCode NICHT 2xx ist.
// Nützlich wenn du den Fehlerfall nicht selbst behandeln willst:

try
{
    HttpResponseMessage response = await _httpClient.GetAsync(url);
    response.EnsureSuccessStatusCode();  // wirft Exception bei 4xx/5xx

    var data = await response.Content.ReadFromJsonAsync<MyData>();
}
catch (HttpRequestException ex)
{
    // Hier landet man bei Netzwerkfehler UND bei 4xx/5xx
    Console.WriteLine($"Request fehlgeschlagen: {ex.StatusCode} – {ex.Message}");
}
```

**⚠️ Nachteil:** Du verlierst die Möglichkeit, den Error-Body zu lesen, weil die Exception
geworfen wird bevor du `ReadAsStringAsync()` aufrufen kannst. Für PyScrapper ist
**manuelles Prüfen** per `IsSuccessStatusCode` daher meistens besser.

---

### 4.6 Status Code mit `switch` gezielt behandeln

```csharp
public async Task<Result> FetchVideoAsync(string id)
{
    var response = await _httpClient.GetAsync($"http://localhost:5000/video/{id}");

    return response.StatusCode switch
    {
        HttpStatusCode.OK =>
            new Result(await response.Content.ReadFromJsonAsync<Video>()),

        HttpStatusCode.NotFound =>
            new Result(Error: $"Video '{id}' nicht gefunden"),

        HttpStatusCode.InternalServerError =>
            new Result(Error: "Server-Fehler – bitte später erneut versuchen"),

        _ =>
            new Result(Error: $"Unbekannter Status: {(int)response.StatusCode}")
    };
}
```

---

## 5. Empfohlenes Pattern für PyScrapper

Da PyScrapper einen Python-Backend + C# Avalonia-Frontend hat, empfiehlt sich ein zentraler `ApiService` mit generischer Fehlerbehandlung:

```csharp
public class PyScrapperApiService
{
    private readonly HttpClient _httpClient;
    private const string BaseUrl = "http://localhost:5000";

    public PyScrapperApiService(HttpClient httpClient)
    {
        _httpClient = httpClient;
    }

    // Generische GET-Methode für beliebige Typen
    private async Task<T?> GetAsync<T>(string endpoint)
    {
        try
        {
            var response = await _httpClient.GetAsync($"{BaseUrl}{endpoint}");

            if (!response.IsSuccessStatusCode)
            {
                var err = await response.Content.ReadFromJsonAsync<ErrorResponse>();
                Console.WriteLine($"[API] Fehler {(int)response.StatusCode}: {err?.Error}");
                return default;
            }

            return await response.Content.ReadFromJsonAsync<T>();
        }
        catch (HttpRequestException ex)
        {
            // Netzwerkfehler: Server nicht erreichbar, Timeout, etc.
            Console.WriteLine($"[API] Verbindungsfehler: {ex.Message}");
            return default;
        }
    }

    // Konkrete Methoden bauen auf der generischen auf
    public Task<VideoListResponse?> GetVideosAsync()
        => GetAsync<VideoListResponse>("/videos");

    public Task<Video?> GetVideoByIdAsync(string id)
        => GetAsync<Video>($"/video/{id}");
}
```

**Vorteile dieses Patterns:**
- Fehlerbehandlung nur an einer Stelle
- Einfach erweiterbar um neue Endpoints
- ViewModel bleibt sauber – ruft nur `GetVideosAsync()` auf, ohne sich um HTTP zu kümmern

---

## 6. Checkliste – Häufige Fehler vermeiden

- [ ] `HttpClient` **niemals** per `new` in jeder Methode erstellen
- [ ] Immer `IsSuccessStatusCode` prüfen **bevor** du den Body liest
- [ ] Python gibt immer `jsonify(...)` zurück (nie plain `return "text"`)
- [ ] Status Code explizit mitgeben: `return jsonify(data), 201` nicht nur `return jsonify(data)`
- [ ] Bei Fehlern im Python-Backend den Error-Body als JSON zurückgeben, nicht als HTML
- [ ] `await` nicht vergessen – alle HTTP-Operationen in C# sind async