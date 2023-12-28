import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class CalanderService {
  constructor(private http: HttpClient) {}

  getCalanderImage(): Observable<Blob> {
    // Replace 'url' and 'data' with your actual endpoint and data
    const url =
      'https://strava-github-profile-ag3u40ar5-handsamtws-projects.vercel.app/heatmap?ploy_by=distance&sport_type=Run&theme=RdPu';
    const data = {
      user_id: '658d171cb1bb1760fa589f0c',
      token: '8fbd0751b4733d33628818060485cdc28d982008',
    };

    // Set the headers if needed
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });

    return this.http.post(url, data, {
      headers: headers,
      responseType: 'blob', // This specifies that the response should be treated as a Blob
    });
  }
}
