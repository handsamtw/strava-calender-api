import { Component, OnInit } from '@angular/core';
import { Observable } from 'rxjs';
import { FetchImageService } from 'src/app/fetch-image.service';
@Component({
  selector: 'app-image-loading',
  templateUrl: './image-loading.component.html',
  styleUrls: ['./image-loading.component.css'],
})
export class ImageLoadingComponent implements OnInit {
  imageUrl = '';
  constructor(private fetchImageService: FetchImageService) {}

  ngOnInit() {
    // mock getting result from backend
    this.fetchImageService.fetchImage().subscribe((imageBlob) => {
      this.imageUrl = URL.createObjectURL(imageBlob);
    });

    // window.location.href = 'http://localhost:4200';
  }
}
