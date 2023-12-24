import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { ThemesComponent } from './components/themes/themes.component';
import { SubmitButtonComponent } from './components/submit-button/submit-button.component';
@NgModule({
  declarations: [AppComponent, DashboardComponent, ThemesComponent, SubmitButtonComponent],
  imports: [BrowserModule, AppRoutingModule],
  providers: [],
  bootstrap: [AppComponent],
})
export class AppModule {}
