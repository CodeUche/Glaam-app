'use client';

import { Review } from '@/types';

interface ReviewCardProps {
  review: Review;
}

function StarDisplay({ rating }: { rating: number }) {
  return (
    <div className="flex gap-0.5">
      {[1, 2, 3, 4, 5].map((star) => (
        <svg
          key={star}
          className={`w-4 h-4 ${star <= rating ? 'text-amber-400' : 'text-gray-200'}`}
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
        </svg>
      ))}
    </div>
  );
}

export function ReviewCard({ review }: ReviewCardProps) {
  const formatDate = (dateStr: string) =>
    new Date(dateStr).toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });

  return (
    <div className="border-b border-gray-100 pb-6 mb-6 last:border-0 last:pb-0 last:mb-0">
      <div className="flex items-start justify-between mb-2">
        <div>
          <p className="font-semibold text-gray-900">{review.client_name || 'Client'}</p>
          <div className="flex items-center gap-2 mt-1">
            <StarDisplay rating={review.rating} />
            <span className="text-sm text-gray-400">{formatDate(review.created_at)}</span>
          </div>
        </div>
      </div>

      <p className="text-gray-700 mt-2 leading-relaxed">{review.comment}</p>

      {review.artist_response && (
        <div className="mt-4 ml-4 pl-4 border-l-2 border-rose-200 bg-rose-50 rounded-r-lg p-3">
          <p className="text-sm font-medium text-rose-700 mb-1">Artist Response</p>
          <p className="text-sm text-gray-700">{review.artist_response}</p>
          {review.responded_at && (
            <p className="text-xs text-gray-400 mt-1">{formatDate(review.responded_at)}</p>
          )}
        </div>
      )}
    </div>
  );
}
