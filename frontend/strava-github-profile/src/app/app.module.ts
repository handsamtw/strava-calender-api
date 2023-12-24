import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { ThemesComponent } from './components/themes/themes.component';
import { SubmitButtonComponent } from './components/submit-button/submit-button.component';
import { DisplayCardComponent } from './components/display-card/display-card.component';
import { StravaConnectButtonComponent } from './components/strava-connect-button/strava-connect-button.component';
import { ImageLoadingComponent } from './components/image-loading/image-loading.component';

@NgModule({
  declarations: [
    AppComponent,
    DashboardComponent,
    ThemesComponent,
    SubmitButtonComponent,
    DisplayCardComponent,
    StravaConnectButtonComponent,
    ImageLoadingComponent,
  ],
  imports: [BrowserModule, AppRoutingModule],
  providers: [],
  bootstrap: [AppComponent],
})
export class AppModule {}
