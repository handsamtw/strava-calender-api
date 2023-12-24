import { Component, Input } from '@angular/core';
import { Output, EventEmitter } from '@angular/core';
@Component({
  selector: 'app-themes',
  templateUrl: './themes.component.html',
  styleUrls: ['./themes.component.css'],
})
export class ThemesComponent {
  @Input() options: string[] = [];
  @Output() optionSelected = new EventEmitter<string>();
  selectedIndex = 0;

  ngOnInit() {
    this.selectOption(this.selectedIndex); // Initially selecting the first option
  }

  selectOption(index: number) {
    this.selectedIndex = index;
    this.optionSelected.emit(this.options[index]);
  }
}
