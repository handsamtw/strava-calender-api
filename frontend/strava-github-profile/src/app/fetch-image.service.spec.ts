import { TestBed } from '@angular/core/testing';

import { FetchImageService } from './fetch-image.service';

describe('FetchImageService', () => {
  let service: FetchImageService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(FetchImageService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
