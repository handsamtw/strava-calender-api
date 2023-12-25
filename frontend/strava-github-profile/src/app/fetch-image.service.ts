import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
@Injectable({
  providedIn: 'root',
})
export class FetchImageService {
  constructor(private http: HttpClient) {}
  fetchImage() {
    const backendUrl = 'http://127.0.0.1:8000/6587b6686b54f031cf1147d8';
    return this.http.get(backendUrl, { responseType: 'blob' });
  }
}
