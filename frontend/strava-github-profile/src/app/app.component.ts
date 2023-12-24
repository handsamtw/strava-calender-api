import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
})
export class AppComponent {
  radioOptions = ['Option 1', 'Option 2', 'Option 3']; // Your array of options
  selectedOption: string = '';
  imageResult: string = '';
  onOptionSelected(option: string) {
    this.selectedOption = option;
    console.log('Selected Option:', option);
  }

  onSubmitEvent(result: string) {
    this.imageResult = result;
  }
}
