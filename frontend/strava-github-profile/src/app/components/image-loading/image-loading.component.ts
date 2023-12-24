import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-image-loading',
  templateUrl: './image-loading.component.html',
  styleUrls: ['./image-loading.component.css'],
})
export class ImageLoadingComponent implements OnInit {
  async ngOnInit(): Promise<void> {
    console.log('fetch image from backend');
    // mock getting result from backend
    await new Promise((f) => setTimeout(f, 1000));

    window.location.href = 'http://localhost:4200';
  }
}
