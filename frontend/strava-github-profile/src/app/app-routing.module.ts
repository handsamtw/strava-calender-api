import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { ImageLoadingComponent } from './components/image-loading/image-loading.component';
const routes: Routes = [
  { path: 'dashboard', component: DashboardComponent },
  { path: 'loading', component: ImageLoadingComponent },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule],
})
export class AppRoutingModule {}
