import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
})
export class AppComponent {
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
