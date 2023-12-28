import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { CalanderService } from './services/calander.service';
@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
})
export class AppComponent implements OnInit {
  constructor(
    private http: HttpClient,
    private calanderService: CalanderService
  ) {}
  ngOnInit(): void {
    this.calanderService.getCalanderImage().subscribe(
      (data) => {
        this.createImageFromBlob(data);
      },
      (error) => {
        console.error(error);
      }
    );
  }
  createImageFromBlob(image: Blob) {
    let reader = new FileReader();
    reader.addEventListener(
      'load',
      () => {
        this.imageToShow = reader.result;
      },
      false
    );

    if (image) {
      reader.readAsDataURL(image);
    }
  }
  imageToShow: any;
  selectedTheme = '';
  imageResult: string = '';
  onOptionSelected(selectedTheme: string) {
    this.selectedTheme = selectedTheme;
    console.log('Selected Option:', selectedTheme);
  }

  onSubmitEvent(result: string) {
    this.imageResult = result;
  }
}
